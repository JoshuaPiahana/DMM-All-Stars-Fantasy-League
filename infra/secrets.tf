resource "random_password" "flask_secret" {
  length  = 64
  special = false
}

resource "random_password" "ingest_secret" {
  length  = 32
  special = false
}

# Full PostgreSQL connection URL — injected into App Runner as DATABASE_URL
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "/${var.project}/database-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

# Flask SECRET_KEY
resource "aws_secretsmanager_secret" "flask_secret_key" {
  name                    = "/${var.project}/secret-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "flask_secret_key" {
  secret_id     = aws_secretsmanager_secret.flask_secret_key.id
  secret_string = random_password.flask_secret.result
}

# Shared token for Lambda → App Runner /internal/poll endpoint
resource "aws_secretsmanager_secret" "ingest_secret" {
  name                    = "/${var.project}/ingest-secret"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "ingest_secret" {
  secret_id     = aws_secretsmanager_secret.ingest_secret.id
  secret_string = random_password.ingest_secret.result
}
