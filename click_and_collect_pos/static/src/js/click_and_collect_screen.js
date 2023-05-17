odoo.define('click_and_collect_pos.SaleOrderScreen', function(require) {
	'use strict';
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	var rpc = require('web.rpc');
	// Define a new class that extends PosComponent
	class SaleOrderScreen extends PosComponent {
	     /**
		 * Override the setup method to perform any additional setup logic.
		 */
		setup() {
			super.setup();
		}
		back() {
			this.showScreen('ProductScreen');
		}

		getSaleOrderListLine() {
			var order_line_id = [];
			this.props.click_and_collect.forEach(function(object) {
				if (object.is_click_and_collect == true) {
					order_line_id.push(object)
				}
			})
			return order_line_id
		}

		async onClick(ev) {
			var order_line = ev.target.dataset.id
			await rpc.query({
				'model': 'stock.picking',
				'method': 'action_confirmation_click',
				'args': [order_line],
			}).then(function(result) {
				if (result = true) {
					ev.target.parentNode.parentNode.remove()
				}
			})
			location.reload();

		}

	};
	SaleOrderScreen.template = 'SaleOrderScreen';

	// Register the new SaleOrderScreen component with the POS registry.
	Registries.Component.add(SaleOrderScreen);

	// Export the new SaleOrderScreen class.
	return SaleOrderScreen;
});