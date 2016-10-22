provider "aws" {
  region = "${var.region}"
}

resource "aws_security_group" "default" {
  name = "ogre ${var.env}"

  # SSH access from anywhere
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # http access from anywhere
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # https access from anywhere
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outbound internet access
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "ogre-ec2" {
  ami = "${var.ami}"
  instance_type = "${var.size}"

  security_groups = ["${aws_security_group.default.name}"]
  key_name = "${var.key_name}"

  tags {
    Name = "ogre-${var.env}"
    app = "ogre"
    env = "${var.env}"
  }

  user_data = <<EOH
#cloud-config
preserve_hostname: true
runcmd:
  - export AWS_ACCESS_KEY_ID='${var.AWS_ACCESS_KEY}'
  - export AWS_SECRET_ACCESS_KEY='${var.AWS_SECRET_KEY}'
  - export AWS_DEFAULT_REGION='${var.region}'
  - export ENV='${var.env}'
  - cd /srv/ogre/ogreclient && make release
  - salt-call --local grains.setval env ${var.env}
  - supervisorctl restart 'ogreserver:'
  - /usr/local/bin/acmetool --batch reconcile
  - systemctl restart nginx
EOH

  # associate EIP to the EC2 instance
  provisioner "local-exec" {
    command = <<EOH
      aws ec2 associate-address --instance-id ${aws_instance.ogre-ec2.id} --allocation-id ${var.eip}
EOH
  }
}
