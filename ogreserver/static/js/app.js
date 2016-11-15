if(typeof String.prototype.endsWith !== 'function') {
    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };
}

$(document).ready(function() {
	$('#advanced').click(function() {
		if($('#advanced-form').hasClass('advanced-open')) {
			$('#advanced-form').removeClass('advanced-open');
			$('#advanced-form').addClass('advanced-closed');
		}else{
			$('#advanced-form').removeClass('advanced-closed');
			$('#advanced-form').addClass('advanced-open');
		}
		return false;
	});
});
