#!/usr/bin/env bash
# One-time: create the S3 bucket and DynamoDB table that hold Terraform state.
# Run with an admin AWS profile. Everything after this is applied from CI.
set -euo pipefail

REGION="${AWS_REGION:-ap-southeast-2}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="chops-buddy-tfstate-${ACCOUNT}"
TABLE="chops-buddy-tflock"

aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null || {
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
  aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
}

aws dynamodb describe-table --table-name "$TABLE" >/dev/null 2>&1 || \
  aws dynamodb create-table --table-name "$TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST --region "$REGION" >/dev/null

cat <<EOF
State backend ready.

  bucket: $BUCKET
  table:  $TABLE

Next, from infra/ with the same admin profile (first apply creates the OIDC role CI will use):

  terraform init -backend-config="bucket=$BUCKET" -backend-config="region=$REGION" -backend-config="dynamodb_table=$TABLE"
  terraform apply

Then add repository secrets:
  AWS_ROLE_ARN   = the github_actions_role_arn output
  TF_STATE_BUCKET = $BUCKET
and set the three SSM parameters listed in the ssm_parameter_names output.
EOF
