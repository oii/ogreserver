variable "ami" {}

module "ogre-prod" {
  source = "../terraform"

  env = "prod"
  key_name = "ogre-prod"

  ami = "${var.ami}"
  eip = "eipalloc-f0f46294"
}
