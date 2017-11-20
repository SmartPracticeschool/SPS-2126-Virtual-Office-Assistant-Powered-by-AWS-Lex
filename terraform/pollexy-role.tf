data "aws_iam_policy_document" "pollexy-ec2-assume-role-policy" {
  statement {
    actions = ["sts:AssumeRole"],
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pollexy-role" {
    name = "pollexy-role"
    assume_role_policy = "${data.aws_iam_policy_document.pollexy-ec2-assume-role-policy.json}"
}

resource "aws_iam_policy" "pollexy-role-policy" {
    name        = "pollexy-role-policy"
    description = "IAM policy for Pollexy role"
    policy = <<EOF
{
    "Version": "2012-10-17",
  "Statement": [
   {
            "Sid": "AllAPIActionsOnPollexyPeople",
            "Effect": "Allow",
            "Action": "dynamodb:*",
            "Resource": [
                "arn:aws:dynamodb:us-east-1:${data.aws_caller_identity.current.account_id}:table/PollexyPeople",
                "arn:aws:dynamodb:us-east-1:${data.aws_caller_identity.current.account_id}:table/PollexyLocations",
                "arn:aws:dynamodb:us-east-1:${data.aws_caller_identity.current.account_id}:table/PollexyMessageSchedule",
                "arn:aws:dynamodb:us-east-1:${data.aws_caller_identity.current.account_id}:table/PollexyMessageLibrary"
            ]
        },
        {
            "Sid": "PollexySQS",
            "Effect": "Allow",
            "Action": "sqs:*",
            "Resource": "arn:aws:sqs:us-east-1:${data.aws_caller_identity.current.account_id}:pollexy*"
        }
]
}
EOF
}

resource "aws_iam_role_policy_attachment" "pollexy-role-policy-attachment" {
    role       = "${aws_iam_role.pollexy-role.name}"
    policy_arn = "${aws_iam_policy.pollexy-role-policy.arn}"
}
