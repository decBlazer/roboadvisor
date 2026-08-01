variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name tag"
  type        = string
  default     = "roboadvisor"
}

variable "db_password" {
  description = "PostgreSQL master database password"
  type        = string
  sensitive   = true
  default     = "RoboAdvisorSecurePass2026!"
}
