# SocialMapper Production Infrastructure
# Terraform configuration for AWS EKS cluster with auto-scaling and monitoring

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    bucket = "socialmapper-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
    # Enable state locking with DynamoDB
    dynamodb_table = "socialmapper-terraform-locks"
    encrypt        = true
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "socialmapper"
      ManagedBy   = "terraform"
    }
  }
}

# Random suffix for unique resource naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Local values for reuse
locals {
  name = "${var.cluster_name}-${random_string.suffix.result}"
  
  common_tags = {
    Environment = var.environment
    Project     = "socialmapper"
    ManagedBy   = "terraform"
  }
}