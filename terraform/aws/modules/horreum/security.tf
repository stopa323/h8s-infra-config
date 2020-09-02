#
# Security groups configuration for Horreum ECS service and ALB.
#

resource "aws_security_group" "alb" {
  name        = "${var.project}-horreum-alb-sg"
  description = "Controls access to Horreum ALB"
  vpc_id      = "${var.vpc_id}"

  ingress {
    protocol    = "tcp"
    from_port   = "${var.service_port}"
    to_port     = "${var.service_port}"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    "Env": "${var.environment}"
  }
}

# Restrict traffic to horreum service from ALB only
resource "aws_security_group" "ecs-service" {
  name        = "${var.project}-horreum-service-sg"
  description = "Restricts Horreum service inbound to ALB only"
  vpc_id      = "${var.vpc_id}"

  ingress {
    protocol        = "tcp"
    from_port       = "${var.service_port}"
    to_port         = "${var.service_port}"
    security_groups = ["${aws_security_group.alb.id}"]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    "Env": "${var.environment}"
  }
}
