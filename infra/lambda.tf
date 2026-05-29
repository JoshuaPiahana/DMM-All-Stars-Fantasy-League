# Placeholder deployment package — replaced by CI in Phase 4.
# CI updates the function code with:
#   aws lambda update-function-code \
#     --function-name <name> --zip-file fileb://lambda.zip
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/.lambda_placeholder.zip"

  source {
    content  = "def lambda_handler(event, context): return {'statusCode': 200}"
    filename = "handler.py"
  }
}

resource "aws_lambda_function" "scraper" {
  function_name = "${local.name_prefix}-scraper"
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"
  timeout       = 300
  memory_size   = 256

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      APP_RUNNER_URL    = "https://${aws_apprunner_service.app.service_url}"
      INGEST_SECRET_ARN = aws_secretsmanager_secret.ingest_secret.arn
    }
  }

  # Terraform only manages config (env vars, runtime, timeout).
  # CI manages the actual function code via update-function-code.
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = { Name = "${local.name_prefix}-scraper" }
}
