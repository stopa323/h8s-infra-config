#
# Variables Configuration
#

variable "environment" {
  description = "Environment code (staging | production)"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resources' name tag"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR with 16 bit prefix e.g. 10.0.0.0/16"
  type        = string
}

variable "az_count" {
  description = "Number of AZs to cover in a given AWS region"
  default     = "2"
}
