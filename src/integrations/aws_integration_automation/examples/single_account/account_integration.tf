# Example: AWS Account Integration with Jit
# This example shows how to integrate a single AWS account with Jit

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Single Account Integration Module
module "jit_aws_account_integration" {
  source = "../../"
  
  # Jit API Configuration
  jit_client_id = var.jit_client_id  # Set via environment variable or terraform.tfvars
  jit_secret    = var.jit_secret     # Set via environment variable or terraform.tfvars
  jit_region    = "us"               # Use "eu" for European API endpoint
  
  # Integration Configuration
  integration_type        = "account"
  aws_regions_to_monitor = var.regions_to_monitor
  
  # Stack Configuration
  stack_name            = "JitAccountIntegration"
  account_name         = var.account_name          # Optional: Display name in Jit platform
  resource_name_prefix = var.resource_name_prefix  # Optional: Prefix for CloudFormation resources
  
  # CloudFormation Configuration
  capabilities = ["CAPABILITY_NAMED_IAM"]
}
