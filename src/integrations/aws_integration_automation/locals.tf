locals {
  # JIT API Configuration
  jit_api_endpoint = var.jit_region == "us" ? "https://api.jit.io" : "https://api.eu.jit.io"
  
  # CloudFormation template URLs based on integration type
  cloudformation_template_url = var.integration_type == "org" ? "https://jit-aws-prod.s3.amazonaws.com/jit_aws_org_integration_stack.json" : "https://jit-aws-prod.s3.amazonaws.com/jit_aws_integration_stack.json"
  
  # Resource name prefix with integration-specific defaults
  resource_name_prefix = var.resource_name_prefix != null ? var.resource_name_prefix : (var.integration_type == "org" ? "JitOrg" : "Jit")
  
  # Base extra parameters for state token request
  base_extra_params = {
    regions_to_monitor = var.aws_regions_to_monitor
    integration_type   = var.integration_type
  }
  
  # Additional parameters for organization integration
  org_extra_params = var.integration_type == "org" ? {
    organizationRootId       = var.organization_root_id
    shouldIncludeRootAccount = var.should_include_root_account
  } : {}
  
  # State token request body with correct structure
  state_token_request_body = {
    vendor    = "aws"
    token_ttl = 1440
    extra     = merge(
      local.base_extra_params,
      local.org_extra_params
    )
  }
} 