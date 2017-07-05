.PHONY: help clean dist pyinstaller build-dedrm clean-bitbar fetch-bitbar package-bitbar push-bitbar-s3

AWS_ACCESS_KEY_ID?=error
AWS_SECRET_ACCESS_KEY?=error
AWS_DEFAULT_REGION?=local
ENV?=dev
AWSCLI?=/usr/local/bin/aws

VERSION:=$$(python setup.py --version)
PYTHON35?=$$HOME/.pyenv/versions/3.5.3/bin/python


help:
	@echo 'Usage:'
	@echo '   make clean           remove all build artifacts'
	@echo '   make dist            build python distributable with setuptools'
	@echo '   make release         push ogreclient and dedrm tools to S3'
	@echo '   make build-dedrm     pull latest DeDRM source and build python distributable'


clean:
	@rm -rf ogreclient.egg-info build
	@find . -name "*.spec" -delete

dist: clean build-dedrm
	python setup.py sdist --formats=gztar,zip

build-dedrm:
	@rm -rf /tmp/dedrm
	git clone --branch ogre https://github.com/oii/DeDRM_tools.git /tmp/dedrm
	cd /tmp/dedrm && \
		python setup.py sdist
	@mv /tmp/dedrm/dist/dedrm-*.tar.gz dist/
	echo "DeDRM at $$(ls -1 dist/*.tar.gz)"

pyinstaller: dist
	$(PYTHON35) -m venv /tmp/build
	source /tmp/build/bin/activate && \
		pip install 'pyinstaller>3.2,<3.3' && \
		pip install "dist/ogreclient-$(VERSION).tar.gz" && \
		pip install 'dist/dedrm-6.5.4.tar.gz' && \
		echo "Building ogreclient $(VERSION)" && \
		pyinstaller \
			--clean \
			--noconfirm \
			--onefile \
			--hidden-import=queue \
			--name ogre-$(VERSION) \
			ogreclient/cli.py
	@rm -rf build

release: dist
	cd dist && \
		$(AWSCLI) s3 cp . s3://ogre-dist-$(ENV)-$(AWS_DEFAULT_REGION) --recursive --exclude "*" --include "ogreclient-*" --acl=public-read
	$(AWSCLI) s3 cp dedrm/dist/dedrm-*.tar.gz s3://ogre-dist-$(ENV)-$(AWS_DEFAULT_REGION) --acl=public-read

clean-bitbar:
	@rm -rf dist/BitBar*.{zip,app} dist/bitbar-bundler

fetch-bitbar: clean-bitbar
	@cd dist && \
		curl -O https://raw.githubusercontent.com/matryer/bitbar/master/Scripts/bitbar-bundler && \
		chmod u+x bitbar-bundler && \
		curl -O -L https://github.com/matryer/bitbar/releases/download/v2.0.0-beta10/BitBarDistro-v2.0.0-beta10.zip && \
		unzip -q BitBarDistro-v2.0.0-beta10.zip

package-bitbar: fetch-bitbar
	@cd dist && \
		./bitbar-bundler BitBarDistro.app bitbar-ogreclient.1d.sh
	@cd dist && \
		zip -rq9ym BitBarDistro.zip BitBarDistro.app

push-bitbar-s3:
	$(AWSCLI) s3 cp dist/BitBarDistro.zip s3://ogre-dist-$(ENV)-$(AWS_DEFAULT_REGION) --acl=public-read
