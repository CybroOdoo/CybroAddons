odoo.define('website_add_multiple_items_to_cart.addMultiItem', function(require) {
	"use strict";

	// Import required modules
	var ajax = require('web.ajax');
	var publicWidget = require('web.public.widget');
	// Define a public widget to enhance cart functionality
	publicWidget.registry.WebsiteCart = publicWidget.Widget.extend({
		selector: '.o_wsale_products_main_row',

		events: {
			'click .confirm_check': '_onClickCartQuantity',
		},

		// Event handler for adding multiple items to the cart.
		_onClickCartQuantity: function(ev) {
			let self = this;
			// Retrieve current cart quantity using AJAX request
			ajax.jsonRpc('/shop/cart/qty', 'call', {}).then(function(qtyCart) {
				sessionStorage.setItem('website_sale_cart_quantity', qtyCart);
				var crtQty = sessionStorage.getItem('website_sale_cart_quantity');
				// Update displayed cart quantity based on retrieved value
				if (crtQty === 'undefined') {
					self.$el.find('.my_cart_quantity').text(0);
				} else {
					self.$el.find(".my_cart_quantity").text(qtyCart);
				}
				// Collect selected product IDs using checkboxes
				ev.preventDefault();
				var result = [];
				var checkBoxes = self.$el[0].querySelectorAll('.mycheckbox');
				checkBoxes.forEach(item => {
					if (item.checked) {
						result.push(item.value);
					}
				});
				// Prepare data for adding selected products to cart using AJAX
				var res = result.map(x => ({
					product_id: x
				}));
				$.ajax({
					type: "get",
					url: "/shop/cart/add_multi_product",
					data: {
						'data': res
					},
					success: function(response) {
						return true;
					}
				});
				// Update total cart quantity in sessionStorage
				if ('website_sale_cart_quantity' in sessionStorage) {
					var currentCartQty = sessionStorage.getItem('website_sale_cart_quantity');
					sessionStorage.setItem('website_sale_cart_quantity', JSON.stringify(Number(currentCartQty) + result.length));
				}
				// Redirect to the '/shop' page after adding items to cart
				window.location = '/shop';
			});
		},
	});
});
