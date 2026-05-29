resource "aws_apprunner_vpc_connector" "main" {
  vpc_connector_name = "${local.name_prefix}-connector"
  subnets            = aws_subnet.private[*].id
  security_groups    = [aws_security_group.apprunner_connector.id]
}

resource "aws_apprunner_service" "app" {
  service_name = local.name_prefix

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr.arn
    }

    # On first apply, the ECR repo exists but has no image yet.
    # Run: terraform apply -target=aws_ecr_repository.app
    # Then push the Docker image, then: terraform apply
    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = tostring(var.app_port)

        runtime_environment_variables = {
          FLASK_CONFIG = "production"
        }

        # App Runner injects these as env vars by fetching from Secrets Manager at startup
        runtime_environment_secrets = {
          DATABASE_URL  = aws_secretsmanager_secret.database_url.arn
          SECRET_KEY    = aws_secretsmanager_secret.flask_secret_key.arn
          INGEST_SECRET = aws_secretsmanager_secret.ingest_secret.arn
        }
      }
    }

    # Auto-deploys whenever a new image is pushed to ECR :latest
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu               = var.app_runner_cpu
    memory            = var.app_runner_memory
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
    ingress_configuration {
      is_publicly_accessible = true
    }
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
    interval = 10
    timeout  = 5
  }

  tags = { Name = local.name_prefix }
}
