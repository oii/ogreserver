variable "AWS_ACCESS_KEY" {}
variable "AWS_SECRET_KEY" {}

module "ogre-prod" {
  source = "../terraform"

  env = "prod"
  key_name = "ogre-prod"

  eip = "eipalloc-f0f46294"
  hostname = "ogre.oii.yt"
  acme-cert-mode = "1"

  AWS_ACCESS_KEY = "${var.AWS_ACCESS_KEY}"
  AWS_SECRET_KEY = "${var.AWS_SECRET_KEY}"
}
