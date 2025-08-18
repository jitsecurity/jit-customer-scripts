# JIT AWS Integration Automation

A Terraform module for automating AWS integration with JIT (Just-in-Time) security platform. This module supports both single AWS account and AWS Organization-wide integrations.

## Features

- **Dual Integration Types**: Support for both single account and organization-wide deployments
- **Multi-Region Support**: Monitor multiple AWS regions simultaneously
- **US/EU API Support**: Compatible with both US and EU JIT API endpoints
- **Error Handling**: Built-in validation and error handling with postconditions

## Integration Types

### Single Account Integration
Deploys JIT integration to a single AWS account using CloudFormation stack.

### Organization Integration
Deploys JIT integration across an entire AWS Organization using a CloudFormation stack that creates internal StackSets, automatically including all current and future accounts in the organization.

## Prerequisites

1. **JIT API Credentials**: Client ID and Secret from JIT platform
2. **AWS Permissions**: Appropriate AWS permissions for CloudFormation operations
3. **Terraform**: Version 1.5 or higher
4. **For Organization Integration**: AWS Organizations service must be enabled

## Quick Start

### Single Account Integration

```hcl
module "jit_aws_account_integration" {
  source = "path/to/aws_integration_automation"
  
  # JIT Configuration
  jit_client_id = var.jit_client_id
  jit_secret    = var.jit_secret
  jit_region    = "us"  # Use "eu" for European API endpoint
  
  # Integration Type
  integration_type = "account"
  
  # AWS Configuration
  aws_regions_to_monitor = ["us-east-1", "us-west-2"]
  
  # Stack Configuration
  stack_name            = "JitAccountIntegration"
  account_name         = "Production Account"
  resource_name_prefix = "JitProd"
  
  # CloudFormation Configuration
  capabilities = ["CAPABILITY_NAMED_IAM"]
}
```

### Organization Integration

```hcl
module "jit_aws_org_integration" {
  source = "path/to/aws_integration_automation"
  
  # JIT Configuration
  jit_client_id = var.jit_client_id
  jit_secret    = var.jit_secret
  jit_region    = "us"  # Use "eu" for European API endpoint
  
  # Integration Type
  integration_type = "org"
  
  # Organization Configuration
  organization_root_id        = "r-xxxxxxxxxxxx"
  should_include_root_account = true
  
  # AWS Configuration
  aws_regions_to_monitor = ["us-east-1", "us-west-2", "eu-west-1"]
  
  # Stack Configuration
  stack_name            = "JitOrgIntegration"
  resource_name_prefix = "JitOrg"
  
  # CloudFormation Configuration
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]
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
| `stack_name` | Name for the CloudFormation stack | `string` | `"JitIntegrationStack"` | no |
| `account_name` | Optional account name alias for Jit platform | `string` | `""` | no |
| `resource_name_prefix` | Prefix for CloudFormation resources (1-40 chars, alphanumeric, hyphens, underscores) | `string` | `null` (auto: "Jit" for account, "JitOrg" for org) | no |
| `organization_root_id` | AWS Organization Root ID (required for org type, format: `r-xxxxxxxxxx`) | `string` | `""` | no |
| `should_include_root_account` | Include root account in organization integration | `bool` | `false` | no |
| `capabilities` | CloudFormation capabilities required | `list(string)` | `["CAPABILITY_NAMED_IAM"]` | no |

## State Token Management

This module implements a **create-only** behavior for the JIT oauth/state-token endpoint using the REST API provider:

1. **First Run**: Creates a new state token via JIT API
2. **Subsequent Runs**: Reuses the existing state token from Terraform state
3. **No Updates**: The state token is never updated or regenerated unless explicitly recreated

### State Token Implementation

The module uses the `restapi_object` resource for state token management:

- Creates state token via JIT API endpoint `/oauth/state-token`
- Stores token in Terraform state automatically
- Uses `ignore_changes` lifecycle rule to prevent updates

### Important Notes

- State token is managed entirely within Terraform state
- Token persists across Terraform runs and is only created once
- To regenerate a state token, you must manually destroy and recreate the `restapi_object.jit_state_token` resource along with the created AWS stack.
- **External ID Persistence**: The state token (external_id) should be created only once. Changing AWS regions, account configurations, or other integration parameters will not affect the existing integration's configuration or regenerate the token
- **External ID Uniqueness**: The external_id is generated by JIT and cannot be reused across integrations. After a successful integration, changing or regenerating the external_id value will cause issues with the existing integration and may break the connection between JIT and your AWS environment
- If you intend to comment out the entire module - it's better to move the restapi provider outside - to allow commenting it out without performing `terraform destroy`.

## CloudFormation Templates

The module automatically selects the appropriate CloudFormation template:

- **Account Integration**: `https://jit-aws-prod.s3.amazonaws.com/jit_aws_integration_stack.json`
- **Organization Integration**: `https://jit-aws-prod.s3.amazonaws.com/jit_aws_org_integration_stack.json`

## Required Capabilities

### Single Account Integration
```terraform
capabilities = ["CAPABILITY_NAMED_IAM"]
```

### Organization Integration
```terraform
capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]
```

The organization integration requires additional capabilities because:
- `CAPABILITY_AUTO_EXPAND`: For creating nested stacks and StackSets within the CloudFormation template
- `CAPABILITY_IAM`: For creating IAM resources
- `CAPABILITY_NAMED_IAM`: For creating IAM resources with custom names

## Resource Name Prefix

The `resource_name_prefix` parameter controls the prefix used for CloudFormation resources:

- **Default for Account Integration**: "Jit"
- **Default for Organization Integration**: "JitOrg"
- **Custom Prefix**: Provide your own prefix (1-40 characters, alphanumeric, hyphens, underscores only)
- **Validation**: The module validates the prefix format automatically

## API Endpoints

The module supports both JIT API regions:

- **US Region**: `https://api.jit.io` (default)
- **EU Region**: `https://api.eu.jit.io`

## Error Handling

The module includes comprehensive error handling:

- **Authentication Validation**: Ensures JIT API authentication succeeds with postconditions
- **Input Validation**: Validates required parameters and formats using Terraform validation blocks
- **Integration Type Validation**: Ensures integration_type is either "account" or "org"
- **Region Validation**: Ensures jit_region is either "us" or "eu"
- **Organization Root ID Validation**: Validates proper format for organization root IDs
- **Lifecycle Management**: Prevents accidental destruction of resources

## Complete Working Examples

The `examples/` directory contains complete working examples organized by integration type:

### Single Account Integration
- **Directory**: [`examples/single_account/`](examples/single_account/)
- **Main File**: `account_integration.tf`
- **Variables**: `variables.tf`
- **Configuration**: `terraform.tfvars`

To use the single account example:
```bash
cd examples/single_account/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### Organization Integration  
- **Directory**: [`examples/aws_organization/`](examples/aws_organization/)
- **Main File**: `organization_integration.tf`
- **Variables**: `variables.tf`
- **Configuration**: `terraform.tfvars`

To use the organization example:
```bash
cd examples/aws_organization/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

## How Organization Integration Works

The organization integration creates a **single CloudFormation stack** that internally:

1. **Creates an IAM Role** for JIT to assume across the organization
2. **Creates a StackSet** (`JitOrganizationsStacksSetRocket`) that automatically deploys to all accounts in the organization
3. **Optionally creates a stack** in the root account if `should_include_root_account = true`

The CloudFormation template handles the StackSet creation and deployment automatically using AWS Organizations' `SERVICE_MANAGED` permission model.

## Security Considerations

1. **Sensitive Variables**: `jit_client_id`, `jit_secret`, and `organization_root_id` are marked as sensitive
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

3. **CloudFormation Capabilities Error**
   - For organization integration, ensure you have all three capabilities: `["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]`
   - For single account integration, use: `["CAPABILITY_NAMED_IAM"]`

4. **CloudFormation Stack Errors**
   - Verify AWS permissions for CloudFormation operations
   - Check CloudFormation events in the AWS console for detailed error messages
   - For organization integration, ensure AWS Organizations service is properly configured

5. **Parameter Validation Errors**
   - Verify `resource_name_prefix` meets length and character requirements (1-40 chars, alphanumeric, hyphens, underscores)
   - Check that `organization_root_id` follows the correct pattern (`r-` followed by 4-32 alphanumeric characters)
   - Ensure `integration_type` is exactly "account" or "org"
   - Ensure `jit_region` is exactly "us" or "eu"

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
| restapi | >= 1.19.1 |

## Contributing

1. Follow existing code patterns and documentation standards
2. Test changes with both integration types using the provided examples
3. Update examples and documentation as needed
4. Ensure all variables have proper validation where applicable

## License

This module is part of the JIT customer scripts repository. Please refer to the main repository license for usage terms. 