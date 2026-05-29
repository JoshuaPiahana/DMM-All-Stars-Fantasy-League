terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Remote state — enable after the one-time bootstrap (see CLAUDE.md):
  #   aws s3 mb s3://dmm-fantasy-tf-state --region us-east-1
  #   aws s3api put-bucket-versioning \
  #     --bucket dmm-fantasy-tf-state \
  #     --versioning-configuration Status=Enabled
  #   aws dynamodb create-table \
  #     --table-name dmm-fantasy-tf-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST \
  #     --region us-east-1
  #
  # backend "s3" {
  #   bucket         = "dmm-fantasy-tf-state"
  #   key            = "production/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "dmm-fantasy-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}
