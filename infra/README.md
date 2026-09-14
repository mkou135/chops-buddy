# infra

Terraform for the AWS side (DECISIONS #7, #8): an ECR repository, an App Runner service that pulls `:latest` from it, the two IAM roles App Runner needs, three SSM SecureString parameters for runtime secrets, and one IAM role that GitHub Actions assumes over OIDC. Supabase (Postgres, Auth) is not managed here.

## One-time setup (Michael, with an admin AWS profile)

1. `./bootstrap.sh` creates the state bucket and lock table and prints the next commands.
2. `terraform init ... && terraform apply` from this directory. The first apply creates the `github_actions_role_arn` that CI uses from then on.
3. Repository secrets:
   - `AWS_ROLE_ARN`: the `github_actions_role_arn` output.
   - `TF_STATE_BUCKET`: printed by bootstrap.
   - `CB_DATABASE_URL_MIGRATIONS`: Supabase **session-mode** pooler URL (port 5432) for Alembic.
   - `ANTHROPIC_API_KEY`: for the weekly evals (already needed by M3).
4. Runtime secrets, set once and never in Terraform state:
   ```bash
   aws ssm put-parameter --overwrite --type SecureString --name /chops-buddy/database_url --value 'postgresql+asyncpg://...:6543/postgres'   # transaction-mode pooler
   aws ssm put-parameter --overwrite --type SecureString --name /chops-buddy/supabase_jwt_secret --value '...'
   aws ssm put-parameter --overwrite --type SecureString --name /chops-buddy/llm_api_key --value 'sk-ant-...'
   ```
   App Runner reads them at start; redeploy the service after changing one.

## What CI does after that

- Every PR touching `api/` or `infra/`: builds the image and smoke-tests `/health`; `terraform fmt`, `validate`, and `plan`.
- Every push to `main`: `terraform apply`, migrations against the live database, image push (`:sha` and `:latest`), then polls App Runner until `/health` reports the new commit (DoD A12).

Without `AWS_ROLE_ARN` set, the AWS steps skip with a warning and only the container smoke test and `terraform validate` run. That is the state of the repo until step 3 is done.

## Cost

App Runner at 0.25 vCPU / 0.5 GB with one provisioned instance is roughly USD 5 to 7 a month idle in Sydney; ECR and SSM are cents. App Runner cannot scale to zero; pause the service from the console between demos if the bill matters.
