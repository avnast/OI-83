import boto3;
import sys;
import httplib;
import socket;

check_timeout = 5

# EC2 server resource
ec2 = boto3.resource('ec2');

def set_check_timeout(t):
	global check_timeout
	check_timeout = t

# some logging
def LOG(message):
	sys.stdout.write(message+"\n");

# function to fetch instance name from tags
def get_instance_name_tag(instance):
	for tag in instance.tags:
		if tag['Key'] == 'Name':
			return tag['Value'];
	return '';

# checks
def check_tcp_port(host, port):
	try:
		sock = socket.create_connection((host, port), check_timeout);
		sock.close();
		return 'OK';
	except Exception as e:
		LOG('WARNING: check_tcp_port({}, {}) failed: {}'.format(host, port, str(e)));
		return 'FAIL';

def check_http(hostname):
	conn = httplib.HTTPConnection(hostname, 80, 0, check_timeout);
	try:
		conn.request("HEAD", '/');
		res = conn.getresponse();
		if res.status == 200:
			return 'OK';
		else:
			LOG('WARNING: http_check(http://{}/) failed with status = {}'.format(hostname, res.status));
			return 'FAIL';
	except Exception as e:
		LOG('WARNING: http_check({}) failed: {}'.format(hostname, str(e)));
		return 'FAIL';

# get EC2 by DNS record
def get_ec2_instance_by_hostname(hostname):
	ip = socket.gethostbyname(hostname);
	ec2_res = ec2.instances.filter(Filters=[{'Name': 'ip-address', 'Values': [ip]}]);
	for instance in ec2_res:
		return instance;
	return None;

# convert tags to filters array for EC2 filtering
def tags2filters(tags):
	tag_keys = []
	filters = []
	for tag in tags:
		tag_keys.append(tag['Key'])
		if tag['Value'] is None:
			continue
		filters.append({
			'Name' : 'tag:'+tag['Key'],
			'Values': [ tag['Value'] ]
		})
	filters.append({'Name': 'tag-key', 'Values': tag_keys})

	return filters


