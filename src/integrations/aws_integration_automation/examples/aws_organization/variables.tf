
# Variables that should be defined in your root module or terraform.tfvars
variable "jit_client_id" {
  description = "Jit API Client ID"
  type        = string
  sensitive   = true
}

variable "jit_secret" {
  description = "Jit API Secret"
  type        = string
  sensitive   = true
}

variable "organization_root_id" {
  description = "AWS Organization Root ID"
  type        = string
  sensitive   = true
}

variable "should_include_root_account" {
  description = "Whether to include the root account in the monitoring."
  type        = bool
  default     = false
}

variable "regions_to_monitor" {
  description = "AWS regions to monitor using Jit"
  type        = list(string)
}

variable "aws_region" {
  description = "AWS region to deploy the integration to"
  type        = string
}

variable "resource_name_prefix" {
  description = "Prefix for the resource name"
  type        = string
  default     = "JitOrg"
}