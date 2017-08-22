data "terraform_remote_state" "ogre" {
  backend = "s3"

  config {
    region = "${var.region}"
    bucket = "ogre-terraform"
    key    = "ogre-${var.region}-${var.env}"
  }
}
