# Monitoring script for Developer Operations Assignment 1.
# This script runs on the EC2 instance, not on your local computer.



# Ask the EC2 metadata service for a temporary IMDSv2 token.
# Metadata is information AWS makes available to software running on this instance.
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")



# Use the token to retrieve the ID of the EC2 instance running this script.
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)



# free -m reports memory in megabytes. awk selects the second output row and
# calculates used memory as a percentage of total memory. printf formats it to 2 decimal places.
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')



# ps -A lists processes; grep -c . counts its non-empty output lines.
# expr subtracts one to account for the header line in the ps output.
PROCESSES=$(expr $(ps -A | grep -c .) - 1)



# Count the process-list lines that contain the Apache process name, httpd.
HTTPD_PROCESSES=$(ps -A | grep -c httpd)



# df -h / reports disk space for the root filesystem in readable units.
# awk selects the usage percentage from the second row of the df output.
DISKUSAGE=$(df -h / | awk 'NR==2 {print $5}')



# uptime -p prints how long the EC2 instance has been running in a readable format.
UPTIME=$(uptime -p)



# Print a report so the results can be seen in the terminal running the SSH command.
echo "----------------------------------------"
echo "EC2 Instance Monitoring"



# date prints the time when this report was produced.
echo "Time: $(date)"
echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "Number of processes: $PROCESSES"
echo "Disk usage: $DISKUSAGE"
echo "System uptime: $UPTIME"
echo "Apache processes: $HTTPD_PROCESSES"



# If at least one process matched httpd, report that the web server appears to be running.
# -ge means "greater than or equal to" in a Bash test.
if [ "$HTTPD_PROCESSES" -ge 1 ]; then
   echo "Web server is running"
else
   echo "Web server is NOT running"
fi



# systemctl asks Linux about the httpd service. The --quiet option hides output;
# the command's success or failure decides which message is printed.
if systemctl is-active --quiet httpd; then
   echo "Apache service is active"
else
   echo "Apache service is NOT active"
fi



echo "----------------------------------------"

