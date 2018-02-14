#!/usr/bin/python

# import boto3
from util import *

# input params
monitored_ip = '34.216.79.136'

instance_tags = [
	{ 'Key': 'ha_cluster', 'Value': None },
	{ 'Key': 'creator', 'Value': 'aleksei_n' }
]

set_check_timeout(5)

########################### MAIN ######################################

if check_tcp_port(monitored_ip, 22)=='OK' and check_http(monitored_ip)=='OK':
	exit()

LOG('OOPS: monitored_ip {} check failed, switching instance'.format(monitored_ip))

instances = ec2.instances.filter(Filters = tags2filters(instance_tags))

# find available instance from our backups
running_instance = None
failed_instance = None
for instance in instances:
	if instance.public_ip_address == monitored_ip:
		failed_instance = instance
	elif instance.state['Name'] == 'running':
		if check_tcp_port(instance.public_ip_address, 22)=='OK' and check_http(instance.public_ip_address)=='OK':
			running_instance = instance
	else:
		LOG('WARNING: found not running HA cluster node: {}({}), state = {}'.format(instance.id, get_instance_name_tag(instance), instance.state['Name']))

if running_instance is None:
	LOG('CRITICAL: no healthy instances in HA cluster, cannot repair!')
	exit(-1)

LOG('INFO: moving service IP {} to new instance {}({})'.format(monitored_ip, running_instance.id, get_instance_name_tag(running_instance)))

try:
	addresses = list(ec2.classic_addresses.filter(PublicIps = [monitored_ip]))
except:
	addresses = []
if len(addresses) > 0:
	LOG('INFO: classic IP found')
else:
	try:
		addresses = list(ec2.vpc_addresses.filter(PublicIps = [monitored_ip]))
		LOG('INFO: VPC IP found')
	except Exception as e:
		LOG('ERROR: cannot find monitored IP {}: {}'.format(monitored_ip, str(e)))
		exit(-2)

eip = addresses[0]

try:
	eip.associate(InstanceId = running_instance.id)
except Exception as e:
	LOG('ERROR: cannot move service IP: '.str(e))

LOG('INFO: stopping failed instance')
try:
	failed_instance.stop()
	failed_instance.wait_until_stopped()
	LOG('INFO: successfully stopped')
except Exception as e:
	LOG('ERROR: cannot stop failed instance: '.str(e))

