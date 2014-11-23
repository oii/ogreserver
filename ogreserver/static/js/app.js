window.OGRE = {};

$(document).ready(function() {

	var ish_options = {
		loadingClassTarget: '#loading-message',

		_splitUrl: function() {
			// split out non-empty URL parts (handles starting/trailing slash)
			return document.location.pathname.split('/').filter(
				function(s) { return s !== ''; }
			);
		},

		getPageFromUrl: function() {
			// return the infinite scrolling starting page from the URL
			var url_parts = this._splitUrl();
			if(url_parts.length > 2) {
				return url_parts[2];
			}else{
				return null;
			}
		},

		processUrl: function(page) {
			// generate the next URL for infinite scrolling and history
			var url_parts = this._splitUrl();
			if(url_parts.length <= 1) {
				// no search, no page number
				url = '/list/+/' + page;
			}else if(url_parts.length == 2){
				// searching, append page number
				if(!url.endsWith('/')) { url += '/'; }
				url = document.location.pathname + page;
			}else{
				// replace page number
				url_parts[2] = page;
				url = '/'+url_parts.join('/');
			}
			return url;
		},

		loadMore: function(page, done) {
			var url = this.processUrl(page);
			;;; console.log('loadMore '+url);

			$.getJSON(url, function(data){
				$('#loading-message').removeClass('loading');

				// iterate data payload
				for(var i=0; i<data.results.length; i++) {
					obj = data.results[i];
					li = document.createElement('li');
					li.className = 'ebook';
					div1 = document.createElement('div');
					div1.className = 'panel radius';
					$(li).append(div1);
					div2 = document.createElement('div');
					div2.className = 'firstsection';
					$(div1).append(div2);
					a = document.createElement('a');
					a.className = 'title';
					a.href = '/view/'+obj.ebook_id;
					$(a).text(obj.author+' - '+obj.title);
					$(div2).append(a);
					$('#ebook-listing').append(li);
				}

				// HTML5 history API
				window.history.replaceState({}, '', url);

				// seppuku on final page
				if(page == data.pagecount) {
					$('#ebook-listing').infiniteScrollHelper('destroy');
					;;; console.log('destroyed');
					return;
				}
				done();
			})
		}
	};

	;;; console.log('pagecount: '+$('#total-pagecount').val());

	var totalPageCount = $('#total-pagecount').val();

	if(totalPageCount > 1) {
		// parse URL to determine current page to start ISH from
		ish_options.startingPageCount = ish_options.getPageFromUrl();
		;;; console.log('starting page: '+ish_options.startingPageCount);

		// don't init ISH if current-page in url == total-pagecount
		if(ish_options.startingPageCount != totalPageCount) {
			OGRE.ish = new InfiniteScrollHelper($('#ebook-listing')[0], ish_options);
		}
	}
});

if(typeof String.prototype.endsWith !== 'function') {
    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };
}
