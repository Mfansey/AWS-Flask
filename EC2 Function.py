import boto3
import botocore
import paramiko
from boto.manage.cmdshell import sshclient_from_instance


user_data = '''#!/bin/bash
git clone <> && cd <directory> &&   '''


def stop_ec2_instance():
    instance_ids = describe_ec2_instance()
    for i in instance_ids:
        try:
            print ("Stopping EC2 instance {i}"
            resource_ec2 = boto3.client("ec2",region_name="us-east-1")
            resource_ec2.stop_instances(InstanceIds=[i])
            print(f"{i} STOPPED")
        except Exception as e:
            print(e)

def create_ec2_instance():
    try:

        resource_ec2 = boto3.client("ec2",region_name='us-east-1')
        resource_ec2.run_instances(
            ImageId="ami-0d5eff06f840b45e9",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            UserData=user_data,
            KeyName="mkey",
        )
    except Exception as e:
        print(e)


def describe_ec2_instance():
    try:
        resource_ec2 = boto3.client("ec2")
        print(resource_ec2.describe_instances()["Reservations"][0]["Instances"][0]["InstanceId"])
        return str(resource_ec2.describe_instances()["Reservations"][0]["Instances"][0]["InstanceId"])
    except Exception as e:
        print(e)

def get_public_ip(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")


    for reservation in reservations:
        for instance in reservation['Instances']:
            print(instance.get("PublicIpAddress"))

    return instance.get("PublicIpAddress")



create_ec2_instance()
