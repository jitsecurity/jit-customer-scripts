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
