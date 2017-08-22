data "terraform_remote_state" "ogre" {
  backend = "s3"

  config {
    region = "eu-west-1"
    bucket = "ogre-terraform"
    key    = "s3-buckets"
  }
}
