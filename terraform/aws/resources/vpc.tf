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
    "Name": "${var.project}-vpc",
    "Env": "${var.environment}"
  }
}

resource "aws_subnet" "private" {
  count             = "${var.az_count}"
  cidr_block        = "${cidrsubnet(var.vpc_cidr, 8, count.index)}"
  availability_zone = "${data.aws_availability_zones.available.names[count.index]}"
  vpc_id            = "${aws_vpc.main.id}"

  tags = {
    "Name": "${var.project}-private-subnet-${count.index}",
    "Env": "${var.environment}"
  }
}

resource "aws_subnet" "public" {
  # Todo: Extend to one subnet per AZ
  count                   = "${var.az_count}"
  cidr_block              = "${cidrsubnet(var.vpc_cidr, 8, var.az_count + count.index)}"
  availability_zone       = "${data.aws_availability_zones.available.names[count.index]}"
  vpc_id                  = "${aws_vpc.main.id}"
  map_public_ip_on_launch = true

  tags = {
    "Name": "${var.project}-public-subnet-${count.index}",
    "Env": "${var.environment}"
  }
}

# IGW for the public subnet
resource "aws_internet_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"

  tags = {
    "Name": "${var.project}-igw",
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
  count      = "${var.az_count}"
  vpc        = true
  depends_on = [aws_internet_gateway.main]

  tags = {
    "Name": "${var.project}-nat-eip-${count.index}",
    "Env": "${var.environment}"
  }
}

resource "aws_nat_gateway" "gw" {
  count         = "${var.az_count}"
  subnet_id     = "${element(aws_subnet.public.*.id, count.index)}"
  allocation_id = "${element(aws_eip.nat-gw.*.id, count.index)}"

  tags = {
    "Name": "${var.project}-nat-gw-${count.index}",
    "Env": "${var.environment}"
  }
}

# Create a new route table for the private subnets to route non-local traffic
# through the NAT gateway to the internet.
resource "aws_route_table" "private" {
  count  = "${var.az_count}"
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = "${element(aws_nat_gateway.gw.*.id, count.index)}"
  }

  tags = {
    "Name": "${var.project}-nat-rt-${count.index}",
    "Env": "${var.environment}"
  }
}

# Explicitely associate the newly created route tables to the private subnets,
# so they don't default to the main route table.
resource "aws_route_table_association" "private" {
  count          = "${var.az_count}"
  subnet_id      = "${element(aws_subnet.private.*.id, count.index)}"
  route_table_id = "${element(aws_route_table.private.*.id, count.index)}"
}
