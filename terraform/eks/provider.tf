#
# Provider Configuration
#

provider "aws" {
  region  = "eu-west-1"
  version = ">= 2.38.0"
}

# Use region configured in provider
data "aws_region" "current" {}

data "aws_availability_zones" "available" { state = "available" }
