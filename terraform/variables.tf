variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS deployment region."
  type        = string
  default     = "eu-central-1"
}

variable "availability_zones" {
  description = "Two Availability Zone names used for the public and private subnets."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b"]

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "availability_zones must contain exactly two Availability Zone names."
  }
}

variable "github_repo" {
  description = "GitHub repository allowed to assume the deployment role, in owner/repo format."
  type        = string
}

variable "db_username" {
  description = "Master PostgreSQL username. Supply through a secure Terraform variable source."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master PostgreSQL password. Supply through a secure Terraform variable source."
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email address subscribed to infrastructure alerts."
  type        = string
}

variable "app_image_tag" {
  description = "Container image tag deployed by ECS."
  type        = string
  default     = "latest"
}

variable "app_secret_key" {
  description = "Application SECRET_KEY value. Provide via a secure Terraform variable source."
  type        = string
  sensitive   = true
}

variable "vpc_cidr" {
  description = "IPv4 CIDR block for the application VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial RDS storage in GiB."
  type        = number
  default     = 20
}

variable "ecs_desired_count" {
  description = "Number of ECS tasks to run."
  type        = number
  default     = 2
}

variable "ecs_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 1024
}
