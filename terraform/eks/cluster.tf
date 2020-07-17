# #
# # EKS Cluster Resources
# #  * IAM Role to allow EKS service to manage other AWS services
# #  * EC2 Security Group to allow networking traffic with EKS cluster
# #  * EKS Cluster
# #
#
# resource "aws_iam_role" "ClusterControlPlane" {
#   name = "control-plane"
#
#   assume_role_policy = <<POLICY
# {
#  "Version": "2012-10-17",
#  "Statement": [
#    {
#      "Effect": "Allow",
#      "Principal": {
#        "Service": "eks.amazonaws.com"
#      },
#      "Action": "sts:AssumeRole"
#    }
#  ]
# }
# POLICY
# }
#
# resource "aws_iam_role_policy_attachment" "EKSClusterPolicy" {
#   policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
#   role       = aws_iam_role.ClusterControlPlane.name
# }
#
# resource "aws_iam_role_policy_attachment" "EKSServicePolicy" {
#   policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
#   role       = aws_iam_role.ClusterControlPlane.name
# }
#
# resource "aws_security_group" "ClusterSG" {
#   name        = "ClusterSG"
#   description = "Cluster communication with worker nodes"
#   vpc_id      = aws_vpc.main.id
#
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "sg-eks-test"
#   }
# }
#
# resource "aws_eks_cluster" "Main" {
#   name     = var.EKSClusterName
#   role_arn = aws_iam_role.ClusterControlPlane.arn
#
#   vpc_config {
#     security_group_ids = [aws_security_group.ClusterSG.id]
#     subnet_ids         = aws_subnet.EKSSubnet[*].id
#   }
#
#   depends_on = [
#     aws_iam_role_policy_attachment.EKSClusterPolicy,
#     aws_iam_role_policy_attachment.EKSServicePolicy,
#   ]
# }
