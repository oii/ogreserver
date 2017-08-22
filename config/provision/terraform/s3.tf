resource "aws_s3_bucket" "s3-backup" {
  bucket = "ogre-backup-${var.env}-${var.region}"
  acl = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "s3-ebooks" {
  bucket = "ogre-ebooks-${var.env}-${var.region}"
  acl = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "s3-static" {
  bucket = "ogre-static-${var.env}-${var.region}"
  acl = "private"
  force_destroy = true
}
