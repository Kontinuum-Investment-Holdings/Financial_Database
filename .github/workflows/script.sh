#!/bin/bash

#	Install dependencies
sudo yum -y install awscli
sudo yum -y install jq
sudo yum -y install zip

#	Create zip file
zip -r code.zip .

#	Set up new EC2 Server
EC2_DATA=$(aws ec2 run-instances --image-id ami-0801a1e12f4a9ccc0 --count 1 --instance-type t2.nano --key-name GitHub_Key_Pair --security-group-ids sg-090a72dbba83bd99c --subnet-id subnet-0b3152f9a9f534b9d)
INSTANCE_ID=$(echo $EC2_DATA | jq -r '.Instances[0].InstanceId')
IP_ADDRESS=$(aws ec2 describe-instances --filters "Name=instance-id,Values=$INSTANCE_ID" | jq -r '.Reservations[0].Instances[0].PublicIpAddress')

#	Download and setup key
aws s3 cp s3://kih-github/GitHub_Key_Pair.pem .
chmod 400 GitHub_Key_Pair.pem

#	Upload file to EC2 server
sftp -i GitHub_Key_Pair.pem  -o StrictHostKeyChecking=no ec2-user@$IP_ADDRESS << EOF
	put code.zip
	exit
EOF

#	Create the deployment package
ssh ec2-user@$IP_ADDRESS -i GitHub_Key_Pair.pem -o StrictHostKeyChecking=no << EOF
	sudo yum -y install zip
	sudo yum -y install unzip
	sudo yum -y install python
	sudo yum -y install python-pip

	unzip code.zip
	rm code.zip

	wget https://github.com/Kontinuum-Investment-Holdings/KIH_API/archive/refs/heads/main.zip
	unzip main.zip -d .
	pip install -r requirements.txt -t .
	pip install -r KIH_API-main/requirements.txt -t .
	mv KIH_API-main/* .

	rm main.zip
	rm -rf KIH_API-main
	rm requirements.txt && rm -rf .github && rm mypy.ini && rm -rf __pycache__ && rm -rf .git
	rm *.bash && rm -rf *.ssh && rm -rf *.cache
	zip -r code.zip .
	exit
EOF

#	Download file to EC2 server
sftp -i GitHub_Key_Pair.pem  -o StrictHostKeyChecking=no ec2-user@$IP_ADDRESS << EOF
	get code.zip
	exit
EOF

#	Terminate EC2 Server
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Upload script to Lambda Function
for function in $LAMBDA_FUNCTION_NAMES; do aws lambda update-function-code --function-name $function --zip-file fileb://code.zip; done