#
# VPC Resources:
#  * VPC
#  * Subnets
#  * Internet Gateway
#  * Route Table
#

# Use region configured in provider
data "aws_region" "current" {}

data "aws_availability_zones" "available" { state = "available" }


resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  tags = {
    "Name": "${var.environment_code}-vpc-eks",
    "kubernetes.io/cluster/${var.cluster_name}": "shared",
  }
}

resource "aws_subnet" "eks_subnet" {
  count = 2

  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = "${var.subnet_octets}.${count.index}.0/24"
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.main.id

  tags = map(
    "Name", "${var.environment_code}-eks-subnet-${count.index}",
    "kubernetes.io/cluster/${var.cluster_name}", "shared",
  )
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment_code}-eks-igw"
  }
}

resource "aws_route_table" "main" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "main" {
  count = 2

  subnet_id      = aws_subnet.eks_subnet.*.id[count.index]
  route_table_id = aws_route_table.main.id
}
