# Configure the REST API provider with global headers
provider "restapi" {
  uri                   = local.jit_api_endpoint
  write_returns_object  = true
  create_returns_object = true
  
  headers = {
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer ${jsondecode(data.http.jit_auth.response_body).accessToken}"
  }
}

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


