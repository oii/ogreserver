help:
	@echo 'Usage:'
	@echo '   make local           local build of vagrant box for staging; useful for debugging'
	@echo '   make staging         local build of staging AMI on EC2'
	@echo '   make atlas           start remote Atlas build of staging AMI on EC2'


_info:
	@echo "Building for commit $$(git log -1 --oneline --abbrev-commit | cut -d\  -f 1)"
	@echo "-----"

_check-local:
ifndef SESAME_PASSWORD
	$(error 'You must export SESAME_PASSWORD to build OGRE')
endif

_check-atlas:
ifndef ATLAS_TOKEN
	$(error 'You must export ATLAS_TOKEN to deploy infrastructure')
endif


local: _check-local _info
	cd provision/staging && \
	time packer build -force \
	  -only=vmware-iso \
		-var git_revision="$$(git log -1 --oneline --abbrev-commit | cut -d\  -f 1)" \
		-var sesame_password=$$SESAME_PASSWORD \
		-var salt_version=v2015.8.7 \
		packer.json

staging-create: _check-local _check-atlas _info
	cd provision/staging && \
	time packer build -force \
	  -only=amazon-ebs \
		-var git_revision="$$(git log -1 --oneline --abbrev-commit | cut -d\  -f 1)" \
		-var sesame_password=$$SESAME_PASSWORD \
		-var salt_version=v2015.8.7 \
		packer.json

staging-destroy: _check-atlas
	cd provision/staging && \
		terraform destroy -force

atlas: _check-atlas _info
	cd provision/staging && \
	packer push \
		-var git_revision="$$(git log -1 --oneline --abbrev-commit | cut -d\  -f 1)" \
		atlas.json

staging-latest-ami:
	aws ec2 describe-images --filters "Name=tag:app,Values=ogre" | jq '.Images[0].ImageId' | tr -d '"'

.PHONY: help _info _check-local _check-atlas local staging atlas
