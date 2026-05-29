variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name — used as a prefix for all resource names"
  type        = string
  default     = "dmm-fantasy"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "dmm_fantasy"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "dmm"
}

variable "app_port" {
  description = "Port the Flask app listens on inside the container"
  type        = number
  default     = 8080
}

variable "app_runner_cpu" {
  description = "App Runner vCPU allocation"
  type        = string
  default     = "0.25 vCPU"
}

variable "app_runner_memory" {
  description = "App Runner memory allocation"
  type        = string
  default     = "0.5 GB"
}
