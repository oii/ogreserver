variable "AWS_ACCESS_KEY" {}
variable "AWS_SECRET_KEY" {}
variable "ami" {}

module "ogre-staging" {
  source = "../terraform"

  env = "staging"
  key_name = "ogre-staging"

  ami = "${var.ami}"
  eip = "eipalloc-919226f4"
  hostname = "ogre-staging.oii.yt"
  acme-cert-mode = "2"

  AWS_ACCESS_KEY = "${var.AWS_ACCESS_KEY}"
  AWS_SECRET_KEY = "${var.AWS_SECRET_KEY}"
}

resource "null_resource" "provision-staging" {
  connection {
    host = "${module.ogre-staging.public_ip}"
    user = "admin"
    private_key = "${file("../aws-keys/ogre-staging.pem")}"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo salt-call state.sls create-ogre-user"
    ]
  }
}
