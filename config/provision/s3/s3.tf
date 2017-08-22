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

resource "aws_s3_bucket" "s3-dist" {
  bucket = "ogre-dist-${var.env}-${var.region}"
  acl = "private"
  force_destroy = true
}
