# Minimal VPC — private isolated subnets only.
#
# Architecture:
#   App Runner is a managed service that lives OUTSIDE the VPC. It uses the
#   VPC connector to reach RDS in private subnets. Lambda is also outside the
#   VPC (no NAT gateway needed — saves ~$32/month). Lambda calls the OSRS
#   hiscores API directly and POSTs results to App Runner's /internal/poll
#   endpoint. App Runner then writes to RDS over the VPC connector.

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name_prefix}-vpc" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "${local.name_prefix}-private-${count.index + 1}" }
}

# App Runner VPC connector security group
# Needs outbound to reach RDS; no inbound required.
resource "aws_security_group" "apprunner_connector" {
  name        = "${local.name_prefix}-apprunner-connector"
  description = "Egress for App Runner VPC connector"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-apprunner-connector-sg" }
}

# RDS security group — only accepts Postgres from the App Runner connector SG.
resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds"
  description = "PostgreSQL access from App Runner"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from App Runner VPC connector"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.apprunner_connector.id]
  }

  tags = { Name = "${local.name_prefix}-rds-sg" }
}
