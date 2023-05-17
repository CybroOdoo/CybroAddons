odoo.define('click_and_collect_pos.website_sale_cart', function(require) {
	"use strict"

	var rpc = require('web.rpc');
	var { websiteSaleCart } = require('website_sale.website_sale');

    // using include method and adding events
	websiteSaleCart.include({
		events: _.extend({}, websiteSaleCart.events, {
			'click #is_click_and_collect': '_onClickClickAndCollect',
			'click .session_values': '_onClickPosConfig',
			'click .js_delete_product': '_onClickDeleteProduct',
		}),
		_onClickClickAndCollect: function(ev) {
			var order_id = $(ev.target).data('id')
			var pos_conf = $(ev.currentTarget.parentElement.parentElement).find('.oe_session')
			if ($(ev.target).is(':checked')) {
				pos_conf.removeClass('d-none')
			} else {
				pos_conf.addClass('d-none')
			}
			rpc.query({
				'model': 'sale.order.line',
				'method': 'write',
				'args': [
					[order_id], {
						'is_click_and_collect': ev.currentTarget.checked
					}
				],
			});

		},
		_onClickDeleteProduct: function(ev) {
			ev.preventDefault();
			$(ev.currentTarget).closest('tr').find('.js_quantity').val(0).trigger('change');

		},
		_onClickPosConfig: function(ev) {
			var closest_check = $(ev.currentTarget.parentElement.parentElement).find('.clickandecollect')
			var order_id = closest_check.data('id')
			var session_id = $(ev.target).val()
			rpc.query({
				'model': 'sale.order.line',
				'method': 'write',
				'args': [
					[order_id], {
						'pos_config_id': parseInt(session_id)
					}
				],
			});
		},
	});
})