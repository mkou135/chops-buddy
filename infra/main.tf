# Chops Buddy API on AWS App Runner (DECISIONS #7).
#
# Resources: ECR repository, App Runner service pulling from it, the IAM roles
# App Runner needs, and an OIDC role so GitHub Actions can push images and apply
# this configuration without long-lived keys (DECISIONS #8).
#
# Secrets (database URL, Supabase JWT secret, Anthropic key) live in SSM Parameter
# Store as SecureStrings and are injected as runtime environment secrets. They are
# created here with placeholder values and ignored on later applies, so the real
# values are set once in the console or with `aws ssm put-parameter`.

terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
  backend "s3" {
    # Bucket and table are created by bootstrap.sh; values passed with -backend-config.
    key = "chops-buddy/terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = { project = "chops-buddy", managed_by = "terraform" }
  }
}

data "aws_caller_identity" "current" {}

# --- Container registry ------------------------------------------------------------

resource "aws_ecr_repository" "api" {
  name                 = "${var.name}-api"
  image_tag_mutability = "MUTABLE" # `latest` is re-pointed on every deploy; SHAs are immutable in practice
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "keep the last 20 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 20 }
      action       = { type = "expire" }
    }]
  })
}

# --- Secrets ------------------------------------------------------------------------

locals {
  secrets = {
    database_url        = "CB_DATABASE_URL"
    supabase_jwt_secret = "CB_SUPABASE_JWT_SECRET"
    llm_api_key         = "CB_LLM_API_KEY"
  }
}

resource "aws_ssm_parameter" "secret" {
  for_each = local.secrets
  name     = "/${var.name}/${each.key}"
  type     = "SecureString"
  value    = "REPLACE_ME"
  lifecycle { ignore_changes = [value] }
}

# --- App Runner roles ---------------------------------------------------------------

data "aws_iam_policy_document" "apprunner_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com", "tasks.apprunner.amazonaws.com"]
    }
  }
}

# Lets App Runner pull from ECR.
resource "aws_iam_role" "apprunner_access" {
  name               = "${var.name}-apprunner-access"
  assume_role_policy = data.aws_iam_policy_document.apprunner_assume.json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Lets the running container read its secrets.
resource "aws_iam_role" "apprunner_instance" {
  name               = "${var.name}-apprunner-instance"
  assume_role_policy = data.aws_iam_policy_document.apprunner_assume.json
}

data "aws_iam_policy_document" "read_secrets" {
  statement {
    actions   = ["ssm:GetParameters", "ssm:GetParameter"]
    resources = [for p in aws_ssm_parameter.secret : p.arn]
  }
  statement {
    actions   = ["kms:Decrypt"]
    resources = ["arn:aws:kms:${var.aws_region}:${data.aws_caller_identity.current.account_id}:alias/aws/ssm"]
  }
}

resource "aws_iam_role_policy" "apprunner_instance_secrets" {
  role   = aws_iam_role.apprunner_instance.id
  policy = data.aws_iam_policy_document.read_secrets.json
}

# --- App Runner service -------------------------------------------------------------

resource "aws_apprunner_auto_scaling_configuration_version" "api" {
  auto_scaling_configuration_name = "${var.name}-api"
  min_size                        = 1
  max_size                        = 2
  max_concurrency                 = 50
}

resource "aws_apprunner_service" "api" {
  service_name                   = "${var.name}-api"
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.api.arn

  source_configuration {
    auto_deployments_enabled = true # a new `latest` in ECR redeploys
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }
    image_repository {
      image_repository_type = "ECR"
      image_identifier      = "${aws_ecr_repository.api.repository_url}:latest"
      image_configuration {
        port = "8080"
        runtime_environment_variables = {
          CB_LLM_MODEL = var.llm_model
        }
        runtime_environment_secrets = {
          for key, env in local.secrets : env => aws_ssm_parameter.secret[key].arn
        }
      }
    }
  }

  instance_configuration {
    cpu               = "256"  # 0.25 vCPU
    memory            = "512"  # MB
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  depends_on = [aws_iam_role_policy_attachment.apprunner_ecr]
}
