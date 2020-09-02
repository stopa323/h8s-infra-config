#
# Fargate task & service definition
#

resource "aws_ecs_task_definition" "main" {
  family                   = "horreum"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"

  task_role_arn            = "${aws_iam_role.ecs-task.arn}"
  execution_role_arn       = "${aws_iam_role.ecs-task-exec.arn}"

  container_definitions = templatefile("${path.module}/task-definition.json.tmpl",
    {
      container_name = "${var.container_name}",
      container_image = "${var.container_image}",
      container_port = "${var.service_port}"
    })

  tags = {
    "Name": "${var.project}-horreum-task",
    "Env": "${var.environment}"
  }
}

resource "aws_ecs_service" "main" {
  name            = "${var.project}-horreum-service"
  cluster         = "${var.cluster_id}"
  task_definition = "${aws_ecs_task_definition.main.arn}"
  desired_count   = 1
  launch_type     = "FARGATE"

  depends_on = [aws_alb_listener.main]

  network_configuration {
    security_groups = ["${aws_security_group.ecs-service.id}"]
    subnets         = "${var.private_subnets_id}"
  }

  load_balancer {
    target_group_arn = "${aws_alb_target_group.main.id}"
    container_name   = "${var.container_name}"
    container_port   = "${var.service_port}"
  }
}
