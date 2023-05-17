odoo.define('click_and_collect_pos.SaleOrderButton', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

    // Define a new class that extends PosComponent
	class SaleOrderButton extends PosComponent {

	     /**
		 * Override the setup method to perform any additional setup logic.
		 */
		setup() {
			super.setup();
		}
		async onClick() {
			var self = this;
			var sale_order = [];
			var stock_picking = self.env.pos.stock_picking;
			var session_id = self.env.pos.pos_session.id
			await this.rpc({
				model: 'sale.order.line',
				method: 'search_read',
				args: [],
			}).then(function(result) {
				result.forEach(function(object) {
					if (object.state == 'sale' && session_id == object.pos_config_id[0]) {
						stock_picking.forEach(function(lines) {
							let plan_arr = null;
							plan_arr = lines.move_ids_without_package.flat(1)
							plan_arr.forEach(function(lines) {
								if (object.id == lines.sale_line_id[0]) {
									sale_order.push(object)
								}
							})
						})
					}
				})
				self.showScreen('SaleOrderScreen', {
					click_and_collect: sale_order,
				});
			});
		}
	}
	SaleOrderButton.template = 'click_and_collect_pos.SaleOrderButton';

	Registries.Component.add(SaleOrderButton);

	return SaleOrderButton;
});