variable "ami" {}

module "ogre-staging" {
  source = "../terraform"

  env = "staging"
  key_name = "ogre-staging"

  ami = "${var.ami}"
  eip = "eipalloc-919226f4"
}
