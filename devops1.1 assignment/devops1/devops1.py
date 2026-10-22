# Developer Operations Assignment 1
# Run one step with a command, or run the full workflow with: python3 devops1.py all
# Run from the folder containing this file, vkey.pem and monitoring.sh.


import boto3
import json
import os
import random
import string
import subprocess
import sys
import time
import urllib.request
from datetime import datetime




INSTANCE_TYPE = "t2.nano"
INSTANCE_COUNT = 1  


KEY_NAME = "vkey"  # EC2 key-pair name; do not include .pem
KEY_FILE = "vkey.pem"  # Matching private key file on your computer
SECURITY_GROUP_ID = "sg-0064a5fd3007679ec"
SUBNET_ID = "subnet-0b7ce302c0400a1b5"


NAME_SUFFIX = "jmurphy"  # First initial + surname, lowercase
INITIALS = "JM"  # Used at the start of the AMI name


LOGO_URL = "http://devops.setudemo.net/logo.jpg"
LOGO_FILE = "logo.jpg"
MONITORING_SCRIPT = "monitoring.sh"
URL_FILE = NAME_SUFFIX + "-websites.txt"






# Wait for the website to respond


def wait_for_website(public_ip, attempts=18):
#     User Data can take a few minutes to install Apache and create the page.
    url = "http://" + public_ip


    for attempt in range(attempts):
        try:
            response = urllib.request.urlopen(url, timeout=10)
            status_code = response.getcode()
            response.close()


            if status_code == 200:
                print("Website is responding:", url)
                return True


            print("Website returned HTTP status:", status_code)


        except Exception as error:
            print("Website not ready yet:", error)


        if attempt < attempts - 1:
            print("Trying again in 10 seconds...")
            time.sleep(10)


    print("Website did not respond successfully:", url)
    return False






# Part 1,2 and 3: Create EC2 instance and website
# Command: python3 devops1.py ec2


def create_ec2_website():
    # Ask AWS Systems Manager for the latest AMI ID.
    ssm = boto3.client("ssm")
    ami_parameter = (
        "/aws/service/ami-amazon-linux-latest/"
        "al2023-ami-kernel-default-x86_64"
    )
    ami_id = ssm.get_parameter(Name=ami_parameter)["Parameter"]["Value"]
    print("Amazon Linux 2023 AMI:", ami_id)


    # User Data runs on the instance at first boot. It installs Apache and
    # creates a page displaying the required EC2 metadata.
    user_data = '''#!/bin/bash

sudo yum install -y httpd 
sudo systemctl enable httpd
sudo systemctl start httpd

TOKEN=$(curl -X PUT -s "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)
AMI_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/ami-id)
AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)


echo "<html><body>" > /var/www/html/index.html
echo "<h1>My EC2 Web Server</h1>" >> /var/www/html/index.html
echo "<p>Instance ID: $INSTANCE_ID</p>" >> /var/www/html/index.html
echo "<p>Public IP address: $PUBLIC_IP</p>" >> /var/www/html/index.html
echo "<p>AMI ID: $AMI_ID</p>" >> /var/www/html/index.html
echo "<p>Availability zone: $AZ</p>" >> /var/www/html/index.html
echo "<p>Welcome to my DevOps assignment website.</p>" >> /var/www/html/index.html
echo "</body></html>" >> /var/www/html/index.html


systemctl enable httpd
systemctl start httpd
'''


    # Launch the requested number of instances in the chosen subnet and security group.
    # The subnet must be configured to auto-assign public IPv4 addresses if SSH/HTTP
    # access from the internet is required.
    ec2 = boto3.resource("ec2")
    instances = ec2.create_instances(
        ImageId=ami_id,
        MinCount=INSTANCE_COUNT,
        MaxCount=INSTANCE_COUNT,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SubnetId=SUBNET_ID,
        SecurityGroupIds=[SECURITY_GROUP_ID],
        UserData=user_data,
    )
       # Give each instance a different Name tag.
    for servernum, instance in enumerate(instances, start=1):
        instance.create_tags(
            Tags=[{
                "Key": "Name",
                "Value": "DevOps1-WebServer" + str(servernum)
            }]
        )


        print(
            "Created DevOps1-WebServer" + str(servernum) + ":",
            instance.id
        )


    # Wait for each instance and check its website.
    for instance in instances:
        print("Waiting for instance to reach running state:", instance.id)
        instance.wait_until_running()
        instance.reload()


        for tag in instance.tags or []:
            if tag["Key"] == "Name":
                print(tag["Value"], "is running.")


        public_ip = instance.public_ip_address


        if not public_ip:
            raise RuntimeError(
                "No public IP address was assigned. Check that the subnet "
                "auto-assigns public IPv4 addresses."
            )


        ec2_url = "http://" + public_ip
        print("Instance ID:", instance.id)
        print("Public IP address:", public_ip)
        print("Waiting for the Apache website:", ec2_url)


        if not wait_for_website(public_ip):
            raise RuntimeError(
                "The EC2 website did not start in time for instance "
                + instance.id
            )


        print("EC2 website created:", ec2_url)


    # Return the details of the first instance.


    return instance.id, public_ip, ec2_url




# Part 4: Create S3 bucket and website
# Command: python3 devops1.py s3


def create_s3_website():
    s3 = boto3.resource("s3")


    # Generate six random lowercase letters or digits for the bucket name.
    characters = string.ascii_lowercase + string.digits
    random_part = ""
    for number in range(6):
        random_part = random_part + random.choice(characters)


    bucket_name = random_part + "-" + NAME_SUFFIX
    print("Creating S3 bucket:", bucket_name)


 
    s3.create_bucket(Bucket=bucket_name)
    print("S3 bucket created.")


    s3_url = "http://" + bucket_name + ".s3-website-us-east-1.amazonaws.com"


    # Download the logo provided
    print("Downloading logo.jpg...")
    subprocess.run(["curl", "-fL", LOGO_URL, "-o", LOGO_FILE], check=True)


    # Open the image in binary-read mode and upload it to S3.
    with open(LOGO_FILE, "rb") as logo_file:
        s3.Object(bucket_name, "logo.jpg").put(
            Body=logo_file,
            ContentType="image/jpeg",
        )
    print("Uploaded logo.jpg.")


    # Make a simple HTML page that displays the uploaded image.
    html_page = '''<!DOCTYPE html>
<html>
<head><title>My S3 Website</title></head>
<body>
    <h1>My S3 Website</h1>
    <p>This website is hosted on Amazon S3.</p>
    <img src="logo.jpg" alt="Website logo">
</body>
</html>
'''


    s3.Object(bucket_name, "index.html").put(
        Body=html_page.encode("utf-8"),
        ContentType="text/html",
    )
    print("Uploaded index.html.")


    # Disable the bucket-level public-access block for this public website bucket.
    # This does not override any account-level public-access restrictions.
    s3.meta.client.delete_public_access_block(Bucket=bucket_name)


    # Allow website visitors to download the objects in this bucket.
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::" + bucket_name + "/*",
            }
        ],
    }
    s3.Bucket(bucket_name).Policy().put(Policy=json.dumps(bucket_policy))


    # Configure index.html as the default page for the static website.
    website_configuration = {"IndexDocument": {"Suffix": "index.html"}}
    s3.BucketWebsite(bucket_name).put(
        WebsiteConfiguration=website_configuration
    )


    print("S3 website created:", s3_url)
    print("S3 bucket name:", bucket_name)
    return bucket_name, s3_url






# Part 5: Save the EC2 and S3 website URLs
# Command: python3 devops1.py urls EC2_URL S3_URL


def save_website_urls(ec2_url, s3_url):
    # Write both website addresses to the text file
    with open(URL_FILE, "w", encoding="utf-8") as url_file:
        url_file.write("EC2 website: " + ec2_url + "\n")
        url_file.write("S3 website: " + s3_url + "\n")


    print("Website URLs saved to:", URL_FILE)
    print("EC2 website:", ec2_url)
    print("S3 website:", s3_url)






# Part 6: Copy and run monitoring.sh using SCP and SSH
# Command: python3 devops1.py monitor PUBLIC_IP


def run_monitoring(public_ip):
    # Check that the private key and shell script exist locally.
    if not os.path.isfile(KEY_FILE):
        raise FileNotFoundError("SSH private key file not found: " + KEY_FILE)


    if not os.path.isfile(MONITORING_SCRIPT):
        raise FileNotFoundError("Monitoring script not found: " + MONITORING_SCRIPT)


    remote = "ec2-user@" + public_ip


    # SCP copies the script from this computer to the EC2 instance.
    print("Copying monitoring.sh to EC2...")
    scp_command = [
        "scp",
        "-o", "StrictHostKeyChecking=accept-new",
        "-i", KEY_FILE,
        MONITORING_SCRIPT,
        remote + ":/home/ec2-user/monitoring.sh",
    ]
    subprocess.run(scp_command, check=True)
    print("monitoring.sh copied.")


    # SSH makes the script executable and runs it on the EC2 instance.
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=accept-new",
        "-i", KEY_FILE,
        remote,
        "chmod +x /home/ec2-user/monitoring.sh && /home/ec2-user/monitoring.sh",
    ]
    subprocess.run(ssh_command, check=True)
    print("Monitoring completed.")






# Part 7: Create an AMI
# Command: python3 devops1.py ami INSTANCE_ID PUBLIC_IP


def create_ami(instance_id):
    # The caller checks that the website responds before calling this function.
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    instance.reload()


    if instance.state["Name"] != "running":
        raise RuntimeError("The EC2 instance must be running before creating the AMI.")


    # The assignment's example format is initials-date-microseconds.
    date_and_microseconds = datetime.now().strftime("%Y-%m-%d-%f")
    ami_name = INITIALS + "-" + date_and_microseconds


    print("Creating AMI:", ami_name)
    image = instance.create_image(
        Name=ami_name,
        Description="DevOps Assignment 1 web server",
    )


    print("AMI creation started. AMI ID:", image.id)
    print("AWS may take several minutes to finish creating the AMI.")






# Run all assignment steps in order
# Command: python3 devops1.py all


def run_all():
    # Each function returns the information needed by the following steps.
    instance_id, public_ip, ec2_url = create_ec2_website()
    bucket_name, s3_url = create_s3_website()
    save_website_urls(ec2_url, s3_url)
    run_monitoring(public_ip)


    # Check the website again immediately before creating the AMI.
    if wait_for_website(public_ip):
        create_ami(instance_id)
    else:
        raise RuntimeError("The website is not responding, so the AMI was not created.")






# Command-line help and main function


def show_usage():
    print("Usage: python3 devops1.py COMMAND [arguments]")
    print("Commands:")
    print("  ec2                         Create the EC2 instance and website")
    print("  s3                          Create the S3 bucket and website")
    print("  urls EC2_URL S3_URL         Save both website URLs to a text file")
    print("  monitor PUBLIC_IP            Copy and run monitoring.sh on EC2")
    print("  ami INSTANCE_ID PUBLIC_IP    Check the website, then create an AMI")
    print("  all                          Run all assignment steps in order")
    print("  help                         Show this message")
    print("\nRun commands from the folder containing vkey.pem and monitoring.sh.")




def main():
    if len(sys.argv) < 2:
        show_usage()
        return


    command = sys.argv[1]


    if command == "ec2":
        create_ec2_website()


    elif command == "s3":
        create_s3_website()


    elif command == "urls":
        if len(sys.argv) == 4:
            save_website_urls(sys.argv[2], sys.argv[3])
        else:
            show_usage()


    elif command == "monitor":
        if len(sys.argv) == 3:
            run_monitoring(sys.argv[2])
        else:
            show_usage()


    elif command == "ami":
        if len(sys.argv) == 4:
            if wait_for_website(sys.argv[3]):
                create_ami(sys.argv[2])
            else:
                print("Website is not responding. AMI not created.")
        else:
            show_usage()


    elif command == "all":
        run_all()


    else:
        show_usage()




main()



