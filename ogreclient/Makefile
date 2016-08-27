AWS_ACCESS_KEY_ID?=error
AWS_SECRET_ACCESS_KEY?=error
AWS_DEFAULT_REGION?=local
ENV?=dev


clean:
	@rm -rf dist/ogreclient-* ogreclient.egg-info build

dist: clean
	python setup.py sdist --formats=gztar,zip
	cd dist && \
		aws s3 cp . s3://ogre-dist-$(ENV)-$(AWS_DEFAULT_REGION) --recursive --exclude "*" --include "ogreclient-*" --acl=public-read

.PHONY: clean dist
