terraform {
  version = "~> 0.1"

  backend "s3" {
    region = "eu-west-1"
    bucket = "ogre-terraform"
    key    = "s3-buckets"
  }
}

provider "aws" {
  region = "${var.region}"
  version = "~> 0.1"
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
  - pip install awscli
  - cd /srv/ogre/ogreclient && make release && make push-bitbar-s3
  - salt-call --local grains.setval env ${var.env}
  - supervisorctl restart 'ogreserver:'
  - hostnamectl set-hostname '${var.hostname}'
  - sed -i 's/ogre.oii.yt/${var.hostname}/g' /etc/nginx/sites-available/ogreserver-80.conf
  - sed -i 's/ogre.oii.yt/${var.hostname}/g' /etc/nginx/sites-available/ogreserver-443.conf
  - ln -s /etc/nginx/sites-available/ogreserver-80.conf /etc/nginx/sites-enabled/ogreserver.conf
  - echo ${var.acme-cert-mode} | /usr/local/bin/acmetool quickstart
  - /usr/local/bin/acmetool want '${var.hostname}'
  - systemctl restart nginx
phone_home:
  url: https://liyhaonvah.execute-api.eu-west-1.amazonaws.com/dev
  post:
    - instance_id
    - hostname
    - fqdn
EOH
}

resource "aws_eip_association" "ogre-eip" {
  instance_id = "${aws_instance.ogre-ec2.id}"
  allocation_id = "${var.eip}"
}
