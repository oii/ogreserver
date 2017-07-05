output "public_ip" {
  value = "${aws_eip_association.ogre-eip.public_ip}"
}
