# Authentication with JIT API to get access token
data "http" "jit_auth" {
  url    = "${local.jit_api_endpoint}/authentication/login"
  method = "POST"
  
  request_headers = {
    "Accept"       = "application/json"
    "Content-Type" = "application/json"
  }
  
  request_body = jsonencode({
    clientId = var.jit_client_id
    secret   = var.jit_secret
  })
  
  lifecycle {
    postcondition {
      condition     = self.status_code == 200
      error_message = "JIT authentication failed with status ${self.status_code}"
    }
  }
}

# Create state token using shell script resource
resource "shell_script" "jit_state_token" {
  triggers = {
    client_id        = var.jit_client_id
    integration_type = var.integration_type
    regions          = join(",", var.aws_regions_to_monitor)
    org_root_id      = var.organization_root_id
  }
  
  environment = {
    JIT_API_ENDPOINT      = local.jit_api_endpoint
    STATE_TOKEN_BODY      = jsonencode(local.state_token_request_body)
  }

  sensitive_environment = {
    JIT_AUTH_RESPONSE = data.http.jit_auth.response_body
  }
  
  lifecycle_commands {
    create = <<-EOT
      ACCESS_TOKEN=$(echo "$JIT_AUTH_RESPONSE" | jq -r '.accessToken')
      TOKEN=$(curl -s -X POST "$JIT_API_ENDPOINT/oauth/state-token" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -d "$STATE_TOKEN_BODY" \
        | jq -r '.token')
      echo "{\"token\": \"$TOKEN\"}"
    EOT
    
    delete = "echo 'State token cleanup - no action needed'"
  }
  
  lifecycle {
    ignore_changes = [environment, sensitive_environment]
  }
  
  interpreter = ["/bin/bash", "-c"]
  
  depends_on = [data.http.jit_auth]
}

# CloudFormation Stack for single account integration
resource "aws_cloudformation_stack" "jit_integration_account" {
  count = var.integration_type == "account" ? 1 : 0
  
  name          = var.stack_name
  template_url  = local.cloudformation_template_url
  capabilities  = var.capabilities
  
  parameters = {
    "ExternalId"                = shell_script.jit_state_token.output["token"]
    "ResourceNamePrefix"        = local.resource_name_prefix
    "AccountName"               = var.account_name
    "ShouldIncludeRootAccount"  = tostring(var.should_include_root_account)
  }
  
  lifecycle {
    prevent_destroy = true
  }
  
  depends_on = [
    data.http.jit_auth,
    shell_script.jit_state_token
  ]
}

# CloudFormation StackSet for organization integration
resource "aws_cloudformation_stack_set" "jit_integration_org" {
  count = var.integration_type == "org" ? 1 : 0
  
  name          = var.stack_name
  template_url  = local.cloudformation_template_url
  capabilities  = var.capabilities
  
  parameters = {
    "ExternalId"                = shell_script.jit_state_token.output["token"]
    "ResourceNamePrefix"        = local.resource_name_prefix
    "OrganizationRootId"        = var.organization_root_id
    "ShouldIncludeRootAccount" = tostring(var.should_include_root_account)
  }
  
  # Auto deployment configuration for organization
  auto_deployment {
    enabled                          = true
    retain_stacks_on_account_removal = false
  }
  
  # Permission model for organization deployment
  permission_model = "SERVICE_MANAGED"
  
  lifecycle {
    prevent_destroy = true
  }
  
  depends_on = [
    data.http.jit_auth,
    shell_script.jit_state_token
  ]
}

# StackSet instances for organization integration (deploys to all accounts in org)
resource "aws_cloudformation_stack_set_instance" "jit_integration_org_instance" {
  count = var.integration_type == "org" ? 1 : 0
  
  stack_set_name         = aws_cloudformation_stack_set.jit_integration_org[0].name
  deployment_targets {
    organizational_unit_ids = [var.organization_root_id]
  }
  
  operation_preferences {
    region_concurrency_type = "PARALLEL"
    max_concurrent_percentage = 100
    failure_tolerance_percentage = 10
  }
  
  depends_on = [aws_cloudformation_stack_set.jit_integration_org]
}
