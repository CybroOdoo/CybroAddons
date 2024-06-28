/** @odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
    /**
    * Represents an Exchange Order popup in a point of sale system.
    * This class extends the AbstractAwaitablePopup class and provides functionality
    * for confirming an exchange order. The exchange order allows products to be
    * added or removed from the current order based on the provided order line.
    * @extends AbstractAwaitablePopup
    */
   export class ExchangeOrder extends AbstractAwaitablePopup {
    static template = 'ExchangeOrder';
        setup() {
        // Super the setup function and set props.line and state.line
            super.setup();
            this.orm = useService("orm");
            this.pos = usePos();
            this.props.line = JSON.parse(JSON.stringify(this.env.services.pos.pos_order_line) || '{}')
            var qty = []
            for(var i = 0; i < this.props.order_line.length; i++){
                qty.push(this.props.order_line[i].qty)
            }
            this.state = useState({
                qty:qty,
                line: JSON.parse(JSON.stringify(this.env.services.pos.pos_order_line) || '{}'),
                pos: this.env.services.pos
            });
        }
         async confirm() {
         // Iterate over each line in props.line and add or remove products from the CurrentOrder
            for(var i = 0; i < this.props.order_line.length; i++){
                if(this.state.qty[i] < this.props.order_line[i].qty){
                    this.pos.popup.add(ErrorPopup, {
                        title: 'Exchange order',
                        body: 'The selected product quantity is higher than the actual quantity in the order.'
                    });
                }
                else{
                if (this.props.order_line[i].qty != 0){
                    this.env.services.pos.get_order().add_product(this.env.services.pos.db.get_product_by_id(this.props.order_line[i].product_id), {quantity: - this.props.order_line[i].qty})
                }
                }
            }
            await this.orm.write("pos.order", [this.props.order_id], {
                exchange: true,
            });
            this.env.services.pos.showScreen('ProductScreen');
            // Show the 'ProductScreen' and invoke the confirm method of the parent class
            super.confirm();
        }
    }
