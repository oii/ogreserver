variable "AWS_ACCESS_KEY" {}
variable "AWS_SECRET_KEY" {}

variable "region" {
	default = "eu-west-1"
}
variable "version" {
	default = "latest"
}
variable "eip" {
  default = "eipalloc-919226f4"
}
variable "atlas_name" {
  default = "mafrosis/ogre-staging"
}
variable "env" {
  default = "staging"
}
variable "key_name" {
  default = "ogre-staging"
}
