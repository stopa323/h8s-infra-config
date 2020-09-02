#
# ECS cluster for Hephaestus services
#

resource "aws_ecs_cluster" "main" {
  name = "${var.project}-ecs-cluster"

  tags = {
    "Env": "${var.environment}"
  }
}
