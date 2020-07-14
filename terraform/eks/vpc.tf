#
# VPC Resources
#  * VPC
#  * Subnets
#  * Internet Gateway
#  * Route Table
#

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = map(
    "Name", "vpc-eks-test",
    "kubernetes.io/cluster/${var.EKSClusterName}", "shared",
  )
}

resource "aws_subnet" "EKSSubnet" {
  count = 2

  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = "10.0.${count.index}.0/24"
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.main.id

  tags = map(
    "Name", "subnet-${count.index}-eks-test",
    "kubernetes.io/cluster/${var.EKSClusterName}", "shared",
  )
}

resource "aws_internet_gateway" "INetGateway" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "igw-eks-test"
  }
}

resource "aws_route_table" "default" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.INetGateway.id
  }
}

resource "aws_route_table_association" "main" {
  count = 2

  subnet_id      = aws_subnet.EKSSubnet.*.id[count.index]
  route_table_id = aws_route_table.default.id
}
