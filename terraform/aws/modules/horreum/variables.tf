# Service config

variable "service_port" {
  description = "Port on which Horreum service is listening"
  type        = number
}

variable "cluster_id" {
  description = "ID of Hephaestus ECS cluster"
  type        = string
}

variable "container_name" {
  description = "Name of Horreum task container name"
  type        = string
  default     = "horreum"
}

variable "container_image" {
  description = "Name of Horreum task container image (including tag)"
  type        = string
}

# VPC stuff

variable "vpc_id" {
  description = "ID of Hephaestus VPC"
  type        = string
}

variable "public_subnets_id" {
  description = "Collection of public subnets' IDs for Horreum service ALB"
  type        = list(string)
}

variable "private_subnets_id" {
  description = "Collection of private subnets' IDs for Horreum service task"
  type        = list(string)
}

# Tagging

variable "environment" {
  description = "Environment code (staging | production)"
  type        = string
}

variable "project" {
  description = "Horreum resources' name-tag prefix"
  type        = string
}
