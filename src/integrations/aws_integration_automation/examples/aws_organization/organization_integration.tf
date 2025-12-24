# Example: AWS Organization Integration with Jit
# This example shows how to integrate an entire AWS organization with Jit

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

# Organization Integration Module
module "jit_aws_org_integration" {
  source = "../../"

  # Jit API Configuration
  jit_client_id = var.jit_client_id  # Set via environment variable or terraform.tfvars
  jit_secret    = var.jit_secret     # Set via environment variable or terraform.tfvars
  jit_region    = "us"               # Use "eu" for European API endpoint

  # Integration Configuration
  integration_type        = "org"
  aws_regions_to_monitor = var.regions_to_monitor

  # Organization Configuration
  organization_root_id        = var.organization_root_id          # Your AWS Organization Root ID
  should_include_root_account = var.should_include_root_account   # Whether to include the management account

  # Stack Configuration
  stack_name            = "JitOrgIntegration"
  resource_name_prefix = var.resource_name_prefix                # Optional: Prefix for CloudFormation resources

  # CloudFormation Configuration
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]
}
