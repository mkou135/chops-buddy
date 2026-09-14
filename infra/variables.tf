variable "aws_region" {
  type    = string
  default = "ap-southeast-2" # Sydney
}

variable "name" {
  type    = string
  default = "chops-buddy"
}

variable "github_repo" {
  type        = string
  description = "owner/repo allowed to assume the deploy role"
  default     = "mkou135/chops-buddy"
}

variable "create_github_oidc_provider" {
  type        = bool
  description = "false if the account already has the GitHub OIDC provider"
  default     = true
}

variable "llm_model" {
  type    = string
  default = "claude-opus-5"
}
