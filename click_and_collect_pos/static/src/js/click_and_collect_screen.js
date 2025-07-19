/** @odoo-module */
import { Component} from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

//Creating a new component for sale order screen
export class SaleOrderScreen extends Component {
	     /**
		 * Override the setup method to perform any additional setup logic.
		 */
		static template = "SaleOrderScreen";
		setup() {
			super.setup();
		}
		back() {
			this.env.services.pos.showScreen("ProductScreen");
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
			var stock_picking = await rpc("/web/dataset/call_kw", {
            'model': 'stock.picking',
            'method': 'action_confirmation_click',
            'args': [order_line],
             kwargs: {},
        })
				if (stock_picking = true) {
					ev.target.parentNode.parentNode.remove()
				}
			location.reload();
		}
	};
	registry.category("pos_screens").add("SaleOrderScreen", SaleOrderScreen);
