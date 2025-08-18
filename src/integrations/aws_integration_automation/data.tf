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
