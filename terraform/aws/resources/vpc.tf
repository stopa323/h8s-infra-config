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
    "Name": "${var.name_prefix}-vpc",
    "Env": "${var.environment}"
  }
}

resource "aws_subnet" "private" {
  # Todo: Extend to one subnet per AZ
  count             = 1
  cidr_block        = "${cidrsubnet(var.vpc_cidr, 8, 0)}"
  availability_zone = "${data.aws_availability_zones.available.names[0]}"
  vpc_id            = "${aws_vpc.main.id}"

  tags = {
    "Name": "${var.name_prefix}-private-subnet",
    "Env": "${var.environment}"
  }
}

resource "aws_subnet" "public" {
  # Todo: Extend to one subnet per AZ
  count                   = 1
  cidr_block              = "${cidrsubnet(var.vpc_cidr, 8, 1)}"
  availability_zone       = "${data.aws_availability_zones.available.names[0]}"
  vpc_id                  = "${aws_vpc.main.id}"
  map_public_ip_on_launch = true

  tags = {
    "Name": "${var.name_prefix}-public-subnet",
    "Env": "${var.environment}"
  }
}

# IGW for the public subnet
resource "aws_internet_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"

  tags = {
    "Name": "${var.name_prefix}-igw",
    "Env": "${var.environment}"
  }
}

# Route the public subnet traffic through the IGW
resource "aws_route" "internet_access" {
  route_table_id         = "${aws_vpc.main.main_route_table_id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.main.id}"
}

# Create a NAT gateway with an EIP to get internet connectivity
resource "aws_eip" "nat-gw" {
  # Todo: Create EIP for each NAT gw
  count      = 1
  vpc        = true
  # depends_on = ["aws_internet_gateway.gw"]

  tags = {
    "Name": "${var.name_prefix}-nat-eip",
    "Env": "${var.environment}"
  }
}

resource "aws_nat_gateway" "gw" {
  # Todo: Create NAT gw in each subnet
  count         = 1
  subnet_id     = "${aws_subnet.public[0].id}"
  allocation_id = "${aws_eip.nat-gw[0].id}"

  tags = {
    "Name": "${var.name_prefix}-nat-gw",
    "Env": "${var.environment}"
  }
}

# Create a new route table for the private subnets to route non-local traffic
# through the NAT gateway to the internet.
resource "aws_route_table" "private" {
  # Todo: Create route table for each NAT gw
  count  = 1
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = "${aws_nat_gateway.gw[0].id}"
  }

  tags = {
    "Name": "${var.name_prefix}-nat-rt",
    "Env": "${var.environment}"
  }
}

# Explicitely associate the newly created route tables to the private subnets,
# so they don't default to the main route table.
resource "aws_route_table_association" "private" {
  # Todo: Create association for each subnet
  count          = 1
  subnet_id      = "${aws_subnet.private[0].id}"
  route_table_id = "${aws_route_table.private[0].id}"
}
