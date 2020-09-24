#
# ALB configuration for Horreum ECS service.
#

resource "aws_alb" "main" {
  name            = "${var.project}-horreum-alb"
  subnets         = "${var.public_subnets_id}"
  security_groups = ["${aws_security_group.alb.id}"]

  tags = {
    "Env": "${var.environment}"
  }
}

resource "aws_alb_target_group" "main" {
  name        = "${var.project}-horreum-alb"
  port        = "${var.service_port}"
  protocol    = "HTTP"
  vpc_id      = "${var.vpc_id}"
  target_type = "ip"

  health_check {
    # Todo: Add dedicated endpoint for basic checks
    path     = "/docs"
    port     = "${var.service_port}"
    protocol = "HTTP"
    matcher  = "200"
    timeout  = 10
  }

  tags = {
    "Env": "${var.environment}"
  }
}

# Redirect all traffic from the ALB to the target group
resource "aws_alb_listener" "main" {
  load_balancer_arn = "${aws_alb.main.id}"
  port              = "${var.service_port}"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.main.arn}"
    type             = "forward"
  }
}
