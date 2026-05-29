resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${local.name_prefix}-db-subnet-group" }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_encrypted     = true

  publicly_accessible      = false
  multi_az                 = false
  deletion_protection      = false
  skip_final_snapshot      = true
  delete_automated_backups = true

  tags = { Name = "${local.name_prefix}-db" }
}
