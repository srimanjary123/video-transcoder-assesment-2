data "aws_availability_zones" "available" {}

resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "asg-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "asg-igw"
  }
}

resource "aws_subnet" "public" {
  for_each = { for i, cidr in var.public_subnets : i => cidr }

  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value
  map_public_ip_on_launch = true
  availability_zone       = element(data.aws_availability_zones.available.names, tonumber(each.key))

  tags = {
    Name = "public-${each.key}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table_association" "public_assoc" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}
