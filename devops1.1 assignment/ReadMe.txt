 DevOps Assignment 1

 Setup
Install Python 3 and Boto3, configure AWS credentials, and update `devops1.py` with your key pair, subnet, security group, initials and name suffix. Run from the folder containing `devops1.py`, `vkey.pem` and `monitoring.sh`.

 Run
```bash
python3 devops1.py ec2
python3 devops1.py s3
python3 devops1.py all
```
Use `python3 devops1.py help` to see all commands. The `all` command runs the full workflow in order.

 Features
Creates an EC2 web server using User Data, sets up an S3 static website, saves both URLs, runs `monitoring.sh` over SSH, and creates an AMI after checking the EC2 website.

 Testing and AI use
ChatGPT was used to help explain AWS/Boto3 concepts, organise code, troubleshoot errors, and draft documentation. 

