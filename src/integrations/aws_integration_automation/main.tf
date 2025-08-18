# Create state token using REST API provider
resource "restapi_object" "jit_state_token" {
  path            = "/oauth/state-token"
  create_method   = "POST"
  read_path       = "/oauth/state-token/{id}/echo"
  id_attribute    = "id"
  ignore_changes_to = ["token"]
  # Request body with state token parameters
  data = jsonencode(local.state_token_request_body)
  
  # Ignore changes to data since read endpoint returns different structure
  lifecycle {
    ignore_changes = [data]
  }
  
  depends_on = [data.http.jit_auth]
}

# CloudFormation Stack for single account integration
resource "aws_cloudformation_stack" "jit_integration_account" {
  count = var.integration_type == "account" ? 1 : 0
  
  name          = var.stack_name
  template_url  = local.cloudformation_template_url
  capabilities  = var.capabilities
  
     parameters = {
     "ExternalId"                = jsondecode(restapi_object.jit_state_token.create_response)["token"]
     "ResourceNamePrefix"        = local.resource_name_prefix
     "AccountName"               = var.account_name
     "ShouldIncludeRootAccount"  = tostring(var.should_include_root_account)
   }
  
  lifecycle {
    prevent_destroy = true
  }
  
  depends_on = [
    data.http.jit_auth,
    restapi_object.jit_state_token
  ]
}

# CloudFormation Stack for organization integration
resource "aws_cloudformation_stack" "jit_integration_org" {
  count = var.integration_type == "org" ? 1 : 0
  
  name          = var.stack_name
  template_url  = local.cloudformation_template_url
  capabilities  = var.capabilities
  
     parameters = {
     "ExternalId"                = jsondecode(restapi_object.jit_state_token.create_response)["token"]
     "ResourceNamePrefix"        = local.resource_name_prefix
     "OrganizationRootId"        = var.organization_root_id
     "ShouldIncludeRootAccount" = tostring(var.should_include_root_account)
   }
  
  lifecycle {
    prevent_destroy = true
  }
  
  depends_on = [
    data.http.jit_auth,
    restapi_object.jit_state_token
  ]
}


