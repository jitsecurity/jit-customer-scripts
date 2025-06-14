# JIT API Credentials
# Follow the guide here - https://docs.jit.io/reference/credentials
# Create creds using "Engineering Manager" role
jit_client_id = "JIT_API_KEY_CLIENT_ID"
jit_secret    = "JIT_API_KEY_SECRET" 

# Should manage also the root account in Jit (false to avoid it)
should_include_root_account = true

# The organization's root ID - can be obtained under AWS Organizations -> AWS Accounts
organization_root_id = "r-xxxx"

# AWS regions to monitor using Jit
regions_to_monitor = ["us-east-1", "us-west-2"]

# AWS region to deploy the integration to
aws_region = "us-east-1"

# Prefix for the resource name
resource_name_prefix = "JitOrg"