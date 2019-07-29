odoo.define('buy_now_button.add_qty', function (require) {
"use strict";

	$(function(){
		$('input[name=add_qty]').change(function(){
			var quantity = $('input[name=add_qty]').val();
			var news = $('#update_qty').val(quantity)
		});
	});
});
