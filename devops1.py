
import boto3

def e2cCheck():
    ec2 = boto3.resource('ec2')
    for i in ec2.instaces.all():
        print(i.id,i.state)

def s3Check():
    s3 = boto3.resource('s3')
    for i in s3.buckets.all():
        print(i.name)