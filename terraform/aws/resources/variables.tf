#
# Variables Configuration
#

variable "environment_code" {
  description = "Environment code (s = staging, p = production)"
  type        = string
}

variable "vpc_cidr" {
  description = "Region for EKS cluster"
  type        = string
}

variable "subnet_octets" {
  description = "First two octects of data center subnet e.g. the X.Y in X.Y.0.0"
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}
