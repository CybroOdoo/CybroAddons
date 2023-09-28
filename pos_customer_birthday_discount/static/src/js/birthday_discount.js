/** @odoo-module */

import ActionpadWidget from 'point_of_sale.ActionpadWidget';
import Registries from "point_of_sale.Registries";
import rpc from 'web.rpc';
const discount = (ActionpadWidget) =>
	class extends ActionpadWidget {
		/**
		 * Function isLong is inherited to check if the current day is the birthday
		 * of selected partner and return the result.
		 */
		get isLongName() {
			this.val = 0;
			var self = this
			if (self.env.pos.config.birthday_discount) {
				if (self.props.partner) {
					const systemDate = new Date();

					// Get the individual components of the date
					const year = systemDate.getFullYear();
					const month = systemDate.getMonth() + 1; // Note: months are zero-indexed, so January is 0
					const day = systemDate.getDate();
					const hours = String(systemDate.getHours()).padStart(2, '0'); // Adding leading zero if needed
					const minutes = String(systemDate.getMinutes()).padStart(2, '0'); // Adding leading zero if needed
					const seconds = String(systemDate.getSeconds()).padStart(2, '0'); // Adding leading zero if needed

					// Format the date as a string (you can customize the format as needed)
					const TodayDate = `${year}-${month < 10 ? '0' : ''}${month}-${day < 10 ? '0' : ''}${day}`;

					var orderLines = self.env.pos.selectedOrder.orderlines
					if (self.env.pos.selectedOrder.partner.birthdate == TodayDate) {
						var orderLines = self.env.pos.selectedOrder.orderlines
						self.props.partner['birthday'] = 'True';
						self.first_order = self.env.pos.config.first_order;
						this.check_pos_order().then(() => {
							for (var order_id = 0; order_id < orderLines.length; order_id++) {
								orderLines[order_id].set_discount(self.val);
							}
						})
					} else {
						for (var order_id = 0; order_id < orderLines.length; order_id++) {
							orderLines[order_id].set_discount(0);
						}
					}
				}
			}
			return super.isLongName
		}
		async check_pos_order() {
			var self = this
			await rpc.query({
					model: "pos.config",
					method: "check_pos_order",
					args: [self.props.partner.id, self.first_order]
				})
				.then(function(data) {
					if (data['birthday'] == 'True' && data['order'] == 'False') {
						self.val = Math.round(self.env.pos.config.discount * 100);
					}
				});
		}
	}
Registries.Component.extend(ActionpadWidget, discount);
