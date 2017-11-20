variable "aws_region" {}

provider "aws" {
  region = "${var.aws_region}"
#  shared_credentials_file = "~/.aws/config"
  profile = "pollexy"
}
