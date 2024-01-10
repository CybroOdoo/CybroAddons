odoo.define("website_estimated_delivery_time.estimated_delivery_time", function(require) {
	"use strict";
	// Importing required modules
	var publicWidget = require('web.public.widget');
	var registry = require("@web/core/registry")
	var ajax = require('web.ajax');
	var core = require('web.core');
	/**
	 * Widget for handling the estimated delivery time functionality.
	 */
	var Template = publicWidget.Widget.extend({
		selector: '#search_website_pin_number',
		events: {
			'click #search_button': '_onClickSearchButton'
		},
		/**
		 * Handler for the search button click event.
		 * Retrieves and processes the pin number and product ID.
		 */
		_onClickSearchButton: function() {
			let self = this
			var search_value = self.$el.find("#pin_number").val();
			var product_id = self.$el.find("#product_id").val();
			ajax.jsonRpc('/website_estimated_delivery_time', 'call', {
				'pin_number': search_value,
				'product_id': product_id
			}).then(function(result) {
				if (result.product_base_availability == 'True' || result.website_base_availability == 'True') {
					self.$el.find('#AvailableModal').modal('show');
					self.$el.find('#AvailableModal').find('#message_to_show_available').text(result.available_message)
				} else {
					self.$el.find('#NotAvailableModal').modal('show');
					self.$el.find('#NotAvailableModal').find('#message_to_show_unavailable').text(result.unavailable_message)
				}
			});
		}
	})
	publicWidget.registry.search_pin_number = Template;
	return Template
})
