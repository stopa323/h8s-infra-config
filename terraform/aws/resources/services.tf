#
# Modules for deploying individual services
#
module "horreum" {
  source = "../modules/horreum"

  service_port = "${var.horreum_service_port}"
  cluster_id   = "${aws_ecs_cluster.main.id}"
  container_image = "${var.horreum_image_name}:${var.horreum_image_tag}"

  vpc_id = "${aws_vpc.main.id}"
  public_subnets_id = "${aws_subnet.public.*.id}"
  private_subnets_id = "${aws_subnet.private.*.id}"

  environment = "${var.environment}"
  project = "${var.project}"
}
