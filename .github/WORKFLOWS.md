# GitHub Actions Setup

This directory contains GitHub Actions workflows that replace the Bitbucket Pipelines configuration.

## Workflows

### 1. Quality Checks (`quality-checks.yml`)
- Runs on pull requests and pushes to main
- Performs linting, type checking, and tests
- Ensures code quality before merging

### 2. Version and Deploy (`version-and-deploy.yml`)
- Runs when code is merged to main
- Creates semantic version tags automatically
- Triggers the deployment workflow

### 3. Build and Deploy (`deploy.yml`)
- Runs when a semantic version tag is created (e.g., v1.2.3)
- Builds Docker image and pushes to ECR
- Deploys to Dev, UAT, and Prod environments

## OIDC Authentication Setup

This setup uses GitHub's OIDC provider to authenticate with AWS instead of long-lived access keys. You need to:

1. **Configure AWS Identity Provider** in your AWS account:
   - Add GitHub as an OIDC identity provider
   - Set the provider URL: `https://token.actions.githubusercontent.com`
   - Set the audience: `sts.amazonaws.com`

2. **Create IAM Roles** with trust policies that allow GitHub Actions to assume them

### Example IAM Trust Policy

Here's an example trust policy for your IAM roles:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR-ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/YOUR-REPO:*"
        }
      }
    }
  ]
}
```

Replace `YOUR-ACCOUNT-ID`, `YOUR-ORG`, and `YOUR-REPO` with your actual values.

## Required Secrets

You need to configure the following secrets in your GitHub repository settings:

### AWS Configuration
- `AWS_DEFAULT_REGION`: AWS region (e.g., ap-south-1)
- `KOREFI_AWS_OIDC_ECR_ROLE_ARN`: AWS OIDC role ARN for ECR access
- `ECR_REPOSITORY`: ECR repository name

### Environment-Specific Secrets

#### Dev Environment
- `KOREFI_AWS_OIDC_DEV_ENV`: AWS OIDC role ARN for Dev
- `AWS_ACCOUNT_ID_DEV`: AWS account ID for Dev
- `ECR_REGISTRY_DEV`: ECR registry URL for Dev
- `SECRET_CHARS_DEV`: Secret identifier for Dev

#### UAT Environment
- `KOREFI_AWS_OIDC_UAT`: AWS OIDC role ARN for UAT
- `AWS_ACCOUNT_ID_UAT`: AWS account ID for UAT
- `ECR_REGISTRY_UAT`: ECR registry URL for UAT
- `SECRET_CHARS_UAT`: Secret identifier for UAT

#### Prod Environment
- `KOREFI_AWS_OIDC_PROD`: AWS OIDC role ARN for Prod
- `AWS_ACCOUNT_ID_PROD`: AWS account ID for Prod
- `ECR_REGISTRY_PROD`: ECR registry URL for Prod
- `SECRET_CHARS_PROD`: Secret identifier for Prod

### Service Configuration
- `KOREFI_MICROSERVICE_NAME`: Microservice name
- `KOREFI_MICROSERVICES_CLUSTER`: ECS cluster name

## Required Variables

You can also configure these as repository variables (not secrets):

- `TASK_CPU`: CPU units for ECS task (default: 512 for Dev/UAT, 1024 for Prod)
- `TASK_MEMORY`: Memory for ECS task (default: 1024 for Dev/UAT, 2048 for Prod)

## Environment Protection Rules

Set up environment protection rules for:
- `dev`: Auto-approve
- `uat`: Auto-approve  
- `prod`: Require manual approval

## How It Works

1. **Pull Request**: Quality checks run automatically
2. **Merge to Main**: Version tag is created automatically
3. **Tag Creation**: Triggers build and deployment pipeline
4. **Deployment**: Automatic deployment to Dev and UAT, manual approval for Prod

## Migration from Bitbucket

The main changes from your Bitbucket setup:
- Uses GitHub's OIDC instead of Bitbucket's OIDC
- Environment protection rules for manual approval
- GitHub Actions syntax instead of Bitbucket Pipelines
- Same deployment logic and ECS integration

