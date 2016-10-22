variable "AWS_ACCESS_KEY" {}
variable "AWS_SECRET_KEY" {}
variable "ami" {}

module "ogre-prod" {
  source = "../terraform"

  env = "prod"
  key_name = "ogre-prod"

  ami = "${var.ami}"
  eip = "eipalloc-f0f46294"

  AWS_ACCESS_KEY = "${var.AWS_ACCESS_KEY}"
  AWS_SECRET_KEY = "${var.AWS_SECRET_KEY}"
}
