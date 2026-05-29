output "ecr_repository_url" {
  description = "ECR repository URL — use in docker push and GitHub secret ECR_REPOSITORY"
  value       = aws_ecr_repository.app.repository_url
}

output "app_runner_service_url" {
  description = "Public HTTPS endpoint for the app"
  value       = "https://${aws_apprunner_service.app.service_url}"
}

output "app_runner_service_arn" {
  description = "App Runner service ARN — add as GitHub secret APP_RUNNER_SERVICE_ARN"
  value       = aws_apprunner_service.app.arn
}

output "rds_endpoint" {
  description = "RDS instance hostname (private — only reachable via VPC connector)"
  value       = aws_db_instance.postgres.address
}

output "lambda_function_name" {
  description = "Scraper Lambda function name — used by CI to update function code"
  value       = aws_lambda_function.scraper.function_name
}
