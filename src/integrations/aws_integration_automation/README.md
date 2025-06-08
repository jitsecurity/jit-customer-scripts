# JIT AWS Integration Automation

A Terraform module for automating AWS integration with JIT (Just-in-Time) security platform. This module supports both single AWS account and AWS Organization-wide integrations.

## Features

- **Dual Integration Types**: Support for both single account and organization-wide deployments
- **Native Terraform**: Pure Terraform implementation using `data "http"` resources
- **Create-Only State Token**: Implements proper create-only behavior for JIT oauth/state-token using Terraform state
- **Multi-Region Support**: Monitor multiple AWS regions simultaneously
- **US/EU API Support**: Compatible with both US and EU JIT API endpoints
- **Error Handling**: Built-in validation and error handling with postconditions
- **State Management**: Pure Terraform state management without local file dependencies

## Integration Types

### Single Account Integration
Deploys JIT integration to a single AWS account using CloudFormation stack.

### Organization Integration
Deploys JIT integration across an entire AWS Organization using CloudFormation StackSet, automatically including all current and future accounts in the organization.

## Prerequisites

1. **JIT API Credentials**: Client ID and Secret from JIT platform
2. **AWS Permissions**: Appropriate AWS permissions for CloudFormation operations
3. **Terraform**: Version 1.5 or higher
4. **For Organization Integration**: AWS Organizations service must be enabled

## Quick Start

### Single Account Integration

```hcl
module "jit_aws_integration" {
  source = "path/to/aws_integration_automation"
  
  # JIT Configuration
  jit_client_id = var.jit_client_id
  jit_secret    = var.jit_secret
  jit_region    = "us"
  
  # Integration Type
  integration_type = "account"
  
  # AWS Regions to Monitor
  aws_regions_to_monitor = ["us-east-1", "us-west-2"]
  
  # Optional Configuration
  stack_name            = "JitAccountIntegration"
  account_name         = "Production Account"
  resource_name_prefix = "JitProd"
  
  tags = {
    Environment = "production"
    Owner       = "security-team"
  }
}
```

### Organization Integration

```hcl
module "jit_aws_org_integration" {
  source = "path/to/aws_integration_automation"
  
  # JIT Configuration
  jit_client_id = var.jit_client_id
  jit_secret    = var.jit_secret
  jit_region    = "us"
  
  # Integration Type
  integration_type = "org"
  
  # Organization Configuration
  organization_root_id        = "r-xxxxxxxxxxxx"
  should_include_root_account = true
  
  # AWS Regions to Monitor
  aws_regions_to_monitor = ["us-east-1", "us-west-2", "eu-west-1"]
  
  # Optional Configuration
  resource_name_prefix = "JitOrg"
}
```

## Input Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `jit_client_id` | Client ID for Jit API authentication | `string` | n/a | yes |
| `jit_secret` | Secret for Jit API authentication | `string` | n/a | yes |
| `integration_type` | Type of AWS integration (`account` or `org`) | `string` | n/a | yes |
| `jit_region` | Jit API region (`us` or `eu`) | `string` | `"us"` | no |
| `aws_regions_to_monitor` | List of AWS regions to monitor | `list(string)` | `["us-east-1"]` | no |
| `stack_name` | Name for the CloudFormation stack or stackset | `string` | `"JitIntegrationStack"` | no |
| `account_name` | Optional account name alias for Jit platform | `string` | `""` | no |
| `resource_name_prefix` | Prefix for CloudFormation resources | `string` | `null` (auto: "Jit" for account, "JitOrg" for org) | no |
| `organization_root_id` | AWS Organization Root ID (required for org type) | `string` | `""` | no |
| `should_include_root_account` | Include root account in organization integration | `bool` | `false` | no |
| `capabilities` | CloudFormation capabilities required | `list(string)` | `["CAPABILITY_NAMED_IAM"]` | no |
| `tags` | Tags to apply to CloudFormation resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `integration_type` | Type of integration deployed |
| `jit_api_endpoint` | JIT API endpoint used |
| `cloudformation_template_url` | CloudFormation template URL used |
| `stack_name` | CloudFormation stack/stackset name |
| `account_name` | Account name alias used in Jit platform |
| `resource_name_prefix` | Prefix used for CloudFormation resources |
| `aws_regions_monitored` | List of AWS regions being monitored |
| `cloudformation_stack_id` | Stack ID (account integration only) |
| `cloudformation_stack_arn` | Stack ARN (account integration only) |
| `cloudformation_stackset_id` | StackSet ID (organization integration only) |
| `cloudformation_stackset_arn` | StackSet ARN (organization integration only) |
| `organization_root_id` | Organization Root ID (organization integration only) |
| `state_token_created` | Whether a new state token was created |
| `state_token_flag_created` | Whether state token flag is initialized in Terraform state |
| `state_token_stored` | Whether state token is stored in Terraform state |

## State Token Management

This module implements a **create-only** behavior for the JIT oauth/state-token endpoint using Terraform state management:

1. **First Run**: Creates a new state token and stores it in Terraform state using `terraform_data` resource
2. **Subsequent Runs**: Reuses the existing state token from Terraform state
3. **No Updates**: The state token is never updated or regenerated unless the Terraform state is manually modified

### State Token Implementation

The module uses three key resources for state token management:

- `terraform_data.state_token_flag`: Tracks whether a token has been created
- `data.http.jit_state_token`: Only executes when the flag indicates first creation
- `terraform_data.state_token_storage`: Stores the actual token value in Terraform state

### Important Notes

- State token is managed entirely within Terraform state - no local files required
- Token persists across Terraform runs and is only created once
- To regenerate a state token, you must manually modify or destroy the relevant Terraform state resources

## CloudFormation Templates

The module automatically selects the appropriate CloudFormation template:

- **Account Integration**: `https://jit-aws-prod.s3.amazonaws.com/jit_aws_integration_stack.json`
- **Organization Integration**: `https://jit-aws-prod.s3.amazonaws.com/jit_aws_org_integration_stack.json`

## Resource Name Prefix

The `resource_name_prefix` parameter controls the prefix used for CloudFormation resources:

- **Default for Account Integration**: "Jit"
- **Default for Organization Integration**: "JitOrg"
- **Custom Prefix**: Provide your own prefix (1-40 characters, alphanumeric, hyphens, underscores only)

## API Endpoints

The module supports both JIT API regions:

- **US Region**: `https://api.jit.io` (default)
- **EU Region**: `https://api.eu.jit.io`

## Error Handling

The module includes comprehensive error handling:

- **Authentication Validation**: Ensures JIT API authentication succeeds
- **State Token Validation**: Verifies state token creation
- **Input Validation**: Validates required parameters and formats
- **Lifecycle Management**: Prevents accidental destruction of resources

## Examples

See the `examples/` directory for complete working examples:

- [`examples/account_integration.tf`](examples/account_integration.tf) - Single account integration
- [`examples/organization_integration.tf`](examples/organization_integration.tf) - Organization integration

## Security Considerations

1. **Sensitive Variables**: `jit_client_id` and `jit_secret` are marked as sensitive
2. **State Files**: Ensure Terraform state files are stored securely (e.g., S3 with encryption)
3. **State Token**: Stored in Terraform state - secure your state backend appropriately
4. **IAM Permissions**: Follow principle of least privilege for AWS IAM permissions

## Troubleshooting

### Common Issues

1. **Authentication Failure**
   - Verify JIT client ID and secret are correct
   - Check if the correct JIT region is specified

2. **Organization Root ID Error**
   - Ensure the organization root ID is in the correct format (`r-xxxxxxxxxxxx`)
   - Verify AWS Organizations is enabled and accessible

3. **State Token Issues**
   - Check Terraform state for `terraform_data.state_token_storage` resource
   - Use `terraform state show` to inspect state token resources

4. **CloudFormation Failures**
   - Verify AWS permissions for CloudFormation operations
   - Check CloudFormation events in the AWS console for detailed error messages

5. **Parameter Validation Errors**
   - Verify `resource_name_prefix` meets length and character requirements
   - Check that `organization_root_id` follows the correct pattern for org integration

### Debug Information

Enable Terraform debug logging for detailed troubleshooting:

```bash
export TF_LOG=DEBUG
terraform apply
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5 |
| aws | >= 5.0 |
| http | >= 3.0 |
| local | >= 2.0 |

## Contributing

1. Follow existing code patterns and documentation standards
2. Test changes with both integration types
3. Update examples and documentation as needed
4. Ensure all variables have proper validation where applicable

## License

This module is part of the JIT customer scripts repository. Please refer to the main repository license for usage terms. 