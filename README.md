# Amazon Pollexy BETA
Special needs virtual assistant

## Prerequisites
* Raspberry Pi 3 Model B
* 8GB or larger SD card 

## Step 1: QuickStart Your Pi in Five Easy Steps
1. Download the [latest](https://s3.amazonaws.com/pollexy-public/images/pi_v17.zip) Pollexy image.
2. Download and install [Etcher](https://etcher.io/).
3. Use Etcher to burn the image to the SD card.
4. After the image is burned, go to the root of the SD card and copy `settings.set.EXAMPLE` to `settings.set`.
5. Open the `settings.set` file and set the `ssid`, `wpa-psk`, and `hostname` to the correct values (just put a space between the key and the value).

**Put the SD card and plug it in. As it boots up, it will automatically change the wi-fi settings/host name, and then reboot once.**

## Step 2: Verify That You Can Login
Your IP address and login information is located here:

    https://s3.amazonaws.com/pi-case/<hostname>

**IMPORTANT:** If this file doesn't exist, there may have been a problem with the wi-fi settings. Simply re-create the `settings.set` file and reboot.

## Step 3: Create a Pollexy User Account
1. Create a new user with this policy, and create an access/secret key.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "lex:GetBuiltinIntent",
                "cloudformation:CreateUploadBucket",
                "sqs:ListQueues",
                "cloudformation:ListStacks",
                "lex:GetBots",
                "logs:DescribeLogGroups",
                "lex:GetBuiltinSlotTypes",
                "cloudformation:EstimateTemplateCost",
                "lex:GetIntents",
                "cloudformation:PreviewStackUpdate",
                "logs:DescribeExportTasks",
                "lex:GetSlotTypes",
                "s3:ListAllMyBuckets",
                "cloudformation:DescribeAccountLimits",
                "lex:PostText",
                "s3:HeadBucket",
                "cloudformation:DescribeChangeSet",
                "lex:GetBuiltinIntents",
                "cloudformation:ValidateTemplate",
                "lex:PostContent"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "lex:*",
            "Resource": [
                "arn:aws:lex:*:*:bot:Pollexy*:*",
                "arn:aws:lex:*:*:intent:Pollexy*:",
                "arn:aws:lex:*:*:slottype:Pollexy*:*",
                "arn:aws:lex:*:*:bot-channel:*:*:Pollexy*"
            ]
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": "lambda:*",
            "Resource": "arn:aws:lambda:*:*:function:pollexy*"
        },
        {
            "Sid": "VisualEditor3",
            "Effect": "Allow",
            "Action": "iam:*",
            "Resource": "arn:aws:iam::*:policy/pollexy*"
        },
        {
            "Sid": "VisualEditor4",
            "Effect": "Allow",
            "Action": "iam:*",
            "Resource": "arn:aws:iam::*:role/pollexy*"
        },
        {
            "Sid": "VisualEditor5",
            "Effect": "Allow",
            "Action": "logs:*",
            "Resource": [
                "arn:aws:logs:*:*:log-group:HandlerLogGroup",
                "arn:aws:logs:*:*:log-group:/aws/lambda/pollexy*:*:*"
            ]
        },
        {
            "Sid": "VisualEditor6",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::pollexy*"
        },
        {
            "Sid": "VisualEditor7",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::pollexy*/*"
        },
        {
            "Sid": "VisualEditor8",
            "Effect": "Allow",
            "Action": "cloudformation:*",
            "Resource": "arn:aws:cloudformation:*:*:stack/pollexy*/*"
        },
        {
            "Sid": "VisualEditor9",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::pi-case/*",
                "arn:aws:s3:::pi-case"
            ]
        },
        {
            "Sid": "VisualEditor10",
            "Effect": "Allow",
            "Action": "dynamodb:*",
            "Resource": [
                "arn:aws:dynamodb:*:*:table/PollexyPeople",
                "arn:aws:dynamodb:*:*:table/PollexyLocations",
                "arn:aws:dynamodb:*:*:table/PollexyMessageLibrary",
                "arn:aws:dynamodb:*:*:table/PollexyMessageSchedule"
            ]
        },
        {
            "Sid": "VisualEditor11",
            "Effect": "Allow",
            "Action": "sqs:*",
            "Resource": "arn:aws:sqs:*:*:pollexy*"
        }
    ]
}
```
## Step 4: Configure Pollexy Credentials
*`Amazon Pollexy` is pre-installed and every action uses the `pollexy` command.*

1. Login to the pi.
2. Go to `/root/Amazon-Pollexy` and run this command to update to the latest version:

        $ git pull && ./update.sh
        
3. After you login, run this command to configure AWS security:

        $ pollexy credentials configure ACCESS_KEY SECRET_KEY REGION

## Step 5: Create the Environment
*To keep it simple, `Amazon Pollexy` wraps the necessary terraform commands so that it uses the right profile.*

1. Login to the pi.
2. Change to the `Amazon Pollexy` folder:
        
        $ cd /root/pollexy

2. Run this command to run the terraform plan to verify that everything will build properly:

        $ pollexy terraform plan

     **IMPORTANT:** *If you see any error messages, verify your credentials and double-check that the user policy matches the above policy.*

3. Run this command to build the environment:

        $ pollexy terraform apply

4. Verify that everything installed buy running:
      
        $ pollexy person list
        There are no users in the system.

5. Deploy the Lambda function:

         $ pollexy serverless deploy
