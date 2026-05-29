# ── App Runner ECR access role ────────────────────────────────────────────────
# Used at service creation time to pull images from ECR.
resource "aws_iam_role" "apprunner_ecr" {
  name = "${local.name_prefix}-apprunner-ecr"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "build.apprunner.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_ecr.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# ── App Runner instance role ──────────────────────────────────────────────────
# The role the running Flask process assumes — needs Secrets Manager read access.
resource "aws_iam_role" "apprunner_instance" {
  name = "${local.name_prefix}-apprunner-instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "tasks.apprunner.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "apprunner_secrets" {
  name = "${local.name_prefix}-apprunner-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = [
        aws_secretsmanager_secret.database_url.arn,
        aws_secretsmanager_secret.flask_secret_key.arn,
        aws_secretsmanager_secret.ingest_secret.arn,
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_instance_secrets" {
  role       = aws_iam_role.apprunner_instance.name
  policy_arn = aws_iam_policy.apprunner_secrets.arn
}

# ── Lambda execution role ─────────────────────────────────────────────────────
resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_secrets" {
  name = "${local.name_prefix}-lambda-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.ingest_secret.arn]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda_secrets.arn
}

# ── EventBridge Scheduler execution role ─────────────────────────────────────
resource "aws_iam_role" "scheduler" {
  name = "${local.name_prefix}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "scheduler_invoke_lambda" {
  name = "${local.name_prefix}-scheduler-invoke-lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = [aws_lambda_function.scraper.arn]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_invoke_lambda" {
  role       = aws_iam_role.scheduler.name
  policy_arn = aws_iam_policy.scheduler_invoke_lambda.arn
}
