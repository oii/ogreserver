help:
	@echo 'Usage:'
	@echo '   make build           build ogreserver AMI on EC2'
	@echo '   make up              bring up instance of latest AMI on EC2 (default: staging)'
	@echo '   make destroy         destroy all infrastructure (default: staging)'
	@echo '   make list-amis       display list of AMIs available'
	@echo '   make terraform-init	 init local env to use terraform (runs "remote config" and "get")'


ENV?=staging
SALT_VERSION?=v2016.3.7
DEBUG?=false

# current HEAD commit ref
BUILD_TAG:=$$(git log -1 --abbrev-commit --oneline | cut -d' ' -f1)

# number of commits HEAD is ahead of remote on current branch
COMMITS_AHEAD:=$$(git rev-list --count --left-right 'HEAD...@{upstream}' | cut -d$$'\t' -f1)


_check-local:
ifndef SESAME_PASSWORD
	$(error 'You must export SESAME_PASSWORD to build OGRE')
endif

_check-commits-ahead:
	@if [ $(COMMITS_AHEAD) -gt 0 ]; then \
		echo 'You need to push commits!'; \
		exit 1; \
	fi


build: _check-commits-ahead _check-local
	@echo "Building for commit $(BUILD_TAG)"
	@echo "-----"
	cd provision && \
	time packer build -force \
		-only=amazon-ebs \
		-var git_revision=$(BUILD_TAG) \
		-var sesame_password=$(SESAME_PASSWORD) \
		-var salt_version=$(SALT_VERSION) \
		-var debug=$(DEBUG) \
		packer.json

up:
	cd provision/$(ENV) && \
		terraform init && \
		terraform get && \
		terraform apply

destroy:
	@cd provision/$(ENV) && \
		terraform destroy -force -var ami=null

list-amis:
	@aws ec2 describe-images --filters "Name=tag:app,Values=ogre" | jq -r '.Images[] | .Name + "\t" + .ImageId + "\t" + .CreationDate' | sort -r

terraform-init:
	cd provision/$(ENV) && \
		terraform remote config -backend=s3 -backend-config="bucket=ogre-terraform-$(ENV)-eu-west-1" -backend-config="key=terraform.tfstate" -backend-config="region=eu-west-1" && \
		terraform get


.PHONY: help _check-local _check-commits-ahead build up destroy list-amis
