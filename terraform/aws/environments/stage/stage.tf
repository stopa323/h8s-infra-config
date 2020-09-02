terraform {
  backend "s3" {
    bucket = "h8s-terraform-state-eu-west-1"
    key    = "staging/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region  = "eu-west-1"
  version = ">= 2.38.0"
}

module "main" {
  source = "../../resources"

  environment      = "staging"

  vpc_cidr         = "10.0.0.0/16"

  # Horreum service
  horreum_image_tag = "0.2.0"
}
