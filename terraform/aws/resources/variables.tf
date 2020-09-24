#
# Root module input variables
#

# General

variable "environment" {
  description = "Environment code (staging | production)"
  type        = string
}

variable "project" {
  description = "Project name. Used as prefix for resource name tag"
  type        = string
  default     = "h8s"
}

# VPC configuration

variable "vpc_cidr" {
  description = "CIDR for Hephaestus VPC. Must have 16 bit prefix (e.g. 10.0.0.0/16)"
  type        = string
}

variable "az_count" {
  description = "Number of availability zones to use in a given AWS region"
  default     = "2"
}

# Horreum service configuration

variable "horreum_service_port" {
  description = "Port on which Horreum service is listening"
  type        = number
  default     = 8003
}

variable "horreum_image_name" {
  description = "TBD"
  type        = string
  default     = "stopa323/h8s-horreum"
}

variable "horreum_image_tag" {
  description = "TBD"
  type        = string
}
