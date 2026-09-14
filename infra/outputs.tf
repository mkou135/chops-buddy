output "api_url" {
  value = "https://${aws_apprunner_service.api.service_url}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "github_actions_role_arn" {
  description = "Set as the AWS_ROLE_ARN repository secret"
  value       = aws_iam_role.github_actions.arn
}

output "ssm_parameter_names" {
  description = "Set real values with: aws ssm put-parameter --overwrite --type SecureString --name <name> --value <value>"
  value       = [for p in aws_ssm_parameter.secret : p.name]
}
