clean:
	@mkdir -p ogreserver/static/dist && rm -rf ogreserver/static/dist/*

dev: clean sass_dev js_dev images
	@true

prod: clean sass_prod js_prod images
	@gzip -9 -c ogreserver/static/dist/ogreserver.css > ogreserver/static/dist/ogreserver.css.gz
	@gzip -9 -c ogreserver/static/dist/ogreserver.js > ogreserver/static/dist/ogreserver.js.gz

js_dev:
	@java -jar /usr/local/lib/compiler.jar \
		--compilation_level=WHITESPACE_ONLY \
		--language_in=ECMASCRIPT5 \
		--formatting=PRETTY_PRINT \
		--js_output_file=ogreserver/static/dist/ogreserver.js \
		ogreserver/static/js/*

js_prod:
	@closure-compiler \
		--language=ecma5 \
		--output-format=text \
		ogreserver/static/js/* \
		> ogreserver/static/dist/ogreserver.js

sass_dev:
	@sassc -t expanded \
		-I ogreserver/static/bower_components/foundation-sites/scss \
		-I ogreserver/static/bower_components/motion-ui/src \
		-I ogreserver/static/sass \
		ogreserver/static/sass/app.scss \
		ogreserver/static/dist/ogreserver.css

sass_prod:
	@sassc -t compressed \
		-I ogreserver/static/bower_components/foundation-sites/scss \
		-I ogreserver/static/bower_components/motion-ui/src \
		-I ogreserver/static/sass \
		ogreserver/static/sass/app.scss \
		ogreserver/static/dist/ogreserver.css

images:
	@rm -rf ogreserver/static/dist/images
	@rsync -a ogreserver/static/images ogreserver/static/dist/

.PHONY: clean dev prod gzip js_dev js_prod sass_dev sass_prod images
