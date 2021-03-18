/*
 * Textyle.js - v2.0
 * https://github.com/mycreatesite/Textyle.js
 * MIT licensed
 * Copyright (C) 2019 ma-ya's CREATE
 * https://myscreate.com
 */
(function($){  
	$.fn.textyle = function(options){
		var target = this;
		var targetTxt = target.contents();
		var defaults = {
					duration : 400,
					delay : 100,
					easing : 'swing',
					callback : null
				};
		var setting = $.extend(defaults, options);
		targetTxt.each(function(){
			var texts = $(this);
			if(this.nodeType === 3){
				mkspn(texts);
			}
		});
		function mkspn(texts){
			texts.replaceWith(texts.text().replace(/(\S)/g,'<span>$1</span>'));
		}
		return this.each(function(){
			var len = target.children().length;
			target.css('opacity',1);
			for (var i = 0; i < len; i++) {
				target.children('span:eq('+i+')')
				.delay(setting.delay*i)
				.animate({
					opacity : 1,
					top : 0,
					left : 0,
				},setting.duration,setting.easing,setting.callback);
			};
		});
	};
}( jQuery ));