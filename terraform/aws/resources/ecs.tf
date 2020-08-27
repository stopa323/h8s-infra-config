#
# ECS Resources:
#  * ECS Cluster
#  * ECS Services & Tasks
#
# + ALB
#

### Security

resource "aws_security_group" "horreum-alb" {
  name        = "${var.name_prefix}-horreum-alb-sg"
  description = "Controls access to horreum ALB"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    protocol    = "tcp"
    from_port   = 8003
    to_port     = 8003
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
resource "aws_security_group" "horreum-service" {
  name        = "${var.name_prefix}-horreum-service-sg"
  description = "Allow inbound access from horreum ALB only"
  vpc_id      = "${aws_vpc.main.id}"

  ingress {
    protocol        = "tcp"
    from_port       = 8003
    to_port         = 8003
    security_groups = ["${aws_security_group.horreum-alb.id}"]
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

### ALB

resource "aws_alb" "horreum" {
  name            = "${var.name_prefix}-horreum-alb"
  subnets         = "${aws_subnet.public.*.id}"
  security_groups = ["${aws_security_group.horreum-alb.id}"]

  tags = {
    "Env": "${var.environment}"
  }
}

resource "aws_alb_target_group" "horreum" {
  name        = "${var.name_prefix}-horreum-alb"
  port        = 8003
  protocol    = "HTTP"
  vpc_id      = "${aws_vpc.main.id}"
  target_type = "ip"

  health_check {
    # Todo: Add dedicated endpoint for basic checks
    path     = "/docs"
    port     = 8003
    protocol = "HTTP"
    matcher  = "200"
    timeout  = 10
  }

  tags = {
    "Env": "${var.environment}"
  }
}

# Redirect all traffic from the ALB to the target group
resource "aws_alb_listener" "horreum" {
  load_balancer_arn = "${aws_alb.horreum.id}"
  port              = "8003"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.horreum.id}"
    type             = "forward"
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-ecs-cluster"

  tags = {
    "Env": "${var.environment}"
  }
}

resource "aws_iam_policy" "ecs-task-exec" {
  name        = "test-policy"
  description = "A test policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role" "ecs-task-exec" {
  name = "task-exec"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "test" {
  role       = aws_iam_role.ecs-task-exec.name
  policy_arn = aws_iam_policy.ecs-task-exec.arn
}

resource "aws_ecs_task_definition" "horreum" {
  family                   = "horreum"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"

  execution_role_arn       = "${aws_iam_role.ecs-task-exec.arn}"

  # Todo: (for container definitions)
  #  * Pass ENVs for DynamoDB
  container_definitions = file("${path.cwd}/../../task-definitions/horreum.json")

  tags = {
    "Name": "${var.name_prefix}-task-horreum",
    "Env": "${var.environment}"
  }
}

resource "aws_ecs_service" "main" {
  name            = "${var.name_prefix}-ecs-service-horreum"
  cluster         = "${aws_ecs_cluster.main.id}"
  task_definition = "${aws_ecs_task_definition.horreum.arn}"
  desired_count   = 1
  launch_type     = "FARGATE"

  depends_on = [
    "aws_alb_listener.horreum",
  ]

  network_configuration {
    security_groups = ["${aws_security_group.horreum-service.id}"]
    subnets         = "${aws_subnet.private.*.id}"
  }

  load_balancer {
    target_group_arn = "${aws_alb_target_group.horreum.id}"
    container_name   = "h8s-horreum"
    container_port   = "8003"
  }
}
