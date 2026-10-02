import boto3
ec2 = boto3.resource('ec2')
servernum = 1
new_inst = ec2.create_instances(ImageId = 'ami-0fef201115eefe936',
 MinCount = 1, MaxCount = 1,InstanceType = 't2.nano', """#!/bin/bash
 yum install httpd -y
 systemctl enable httpd
 systemctl start httpd""",
SecurityGroupIds = 'sg-0ce5c987070b7a258',
KeyPair ='mykeyaws'
)

new_inst[0].create_tags(
 Tags = [{'Key' :'Name', 'Value': 'Webserver' +str(servernum)}]
)
servernum += 1

new_inst[0].wait_until_running()
new_inst[0].reload()

print (new_inst[0].id,new_inst[0].public_ip_address)
