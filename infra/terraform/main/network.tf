# A public-subnet-only network: no NAT gateway, no endpoints, no load balancer (planning/02 section 2.4). A
# task gets a public IP at launch and reaches Bedrock, S3, ECR, STS and CloudWatch Logs over HTTPS only.

resource "aws_vpc" "main" {
  cidr_block = "10.42.0.0/16"

  tags = {
    Name = var.project
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = var.project
  }
}

# `Tier = public` is how `hc sweep launch` finds the subnets (src/horizon_compact/sweep/launch.py).
resource "aws_subnet" "public" {
  for_each = {
    "${var.region}a" = "10.42.0.0/24"
    "${var.region}b" = "10.42.1.0/24"
  }

  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.key
  cidr_block              = each.value
  map_public_ip_on_launch = false # RunTask assigns one per task

  tags = {
    Name = "${var.project}-public-${each.key}"
    Tier = "public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project}-public"
  }
}

resource "aws_route" "internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# No ingress. Egress is HTTPS only, to anywhere. DNS to the VPC resolver is not filtered by security groups.
# Rules are inline on purpose: a separate rule resource would need tag-on-create for the rule, and the deploy
# role's tagging permission is scoped to the five resource types that carry tags.
resource "aws_security_group" "sweep" {
  name        = "${var.project}-sweep"
  description = "Sweep tasks: no inbound, outbound HTTPS only"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "HTTPS to Bedrock, S3, ECR, STS and CloudWatch Logs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-sweep"
  }
}
