variable "jit_client_id" {
  description = "Client ID for Jit API authentication"
  type        = string
  sensitive   = true
}

variable "jit_secret" {
  description = "Secret for Jit API authentication"
  type        = string
  sensitive   = true
}

variable "jit_region" {
  description = "Jit API region - determines which endpoint to use"
  type        = string
  default     = "us"
  validation {
    condition     = contains(["us", "eu"], var.jit_region)
    error_message = "The jit_region must be either 'us' or 'eu'."
  }
}

variable "integration_type" {
  description = "Type of AWS integration: 'account' for single account, 'org' for organization"
  type        = string
  validation {
    condition     = contains(["account", "org"], var.integration_type)
    error_message = "The integration_type must be either 'account' or 'org'."
  }
}

variable "aws_regions_to_monitor" {
  description = "List of AWS regions to monitor"
  type        = list(string)
  default     = ["us-east-1"]
}

variable "stack_name" {
  description = "Name for the CloudFormation stack or stackset"
  type        = string
  default     = "JitIntegrationStack"
}

variable "account_name" {
  description = "Optional account name alias to be used in Jit platform. If not provided, the account ID will be displayed."
  type        = string
  default     = ""
}

variable "resource_name_prefix" {
  description = "Prefix to use for the resources created by the CloudFormation template"
  type        = string
  default     = null
  validation {
    condition = var.resource_name_prefix == null || (
      length(var.resource_name_prefix) >= 1 &&
      length(var.resource_name_prefix) <= 40 &&
      can(regex("^[a-zA-Z0-9-_]*$", var.resource_name_prefix))
    )
    error_message = "The resource_name_prefix must be 1-40 characters and contain only alphanumeric characters, hyphens, and underscores."
  }
}

variable "organization_root_id" {
  description = "AWS Organization Root ID (required for org integration type). Must start with 'r-'"
  type        = string
  default     = ""
  validation {
    condition = var.organization_root_id == "" || can(regex("^r-[a-z0-9]{4,32}$", var.organization_root_id))
    error_message = "The organization_root_id must be a valid organization root ID starting with 'r-' followed by 4-32 alphanumeric characters."
  }
}

variable "should_include_root_account" {
  description = "Whether to include the root account in organization integration"
  type        = bool
  default     = false
}

variable "capabilities" {
  description = "CloudFormation capabilities required for stack creation"
  type        = list(string)
  default     = ["CAPABILITY_NAMED_IAM"]
}
