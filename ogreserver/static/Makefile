clean:
	@mkdir -p dist && rm -rf dist/*

dev: clean sass_dev js_dev images
	@true

prod: clean sass_prod js_prod images
	@gzip -9 -c dist/ogreserver.css > dist/ogreserver.css.gz
	@gzip -9 -c dist/ogreserver.js > dist/ogreserver.js.gz

js_dev:
	@closure-compiler \
		--language=ecma6 \
		--pretty \
		js/* \
		> dist/ogreserver.js

js_prod:
	@closure-compiler \
		--language=ecma6 \
		js/* \
		> dist/ogreserver.js

sass_dev:
	@sassc -t expanded \
		-I bower_components/foundation-sites/scss \
		-I bower_components/motion-ui/src \
		-I sass \
		sass/app.scss \
		dist/ogreserver.css

sass_prod:
	@sassc -t compressed \
		-I bower_components/foundation-sites/scss \
		-I bower_components/motion-ui/src \
		-I sass \
		sass/app.scss \
		dist/ogreserver.css

images:
	@rm -rf dist/images
	@rsync -a images dist/

.PHONY: clean dev prod gzip js_dev js_prod sass_dev sass_prod images
