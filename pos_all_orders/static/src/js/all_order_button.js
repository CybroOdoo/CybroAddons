/** @odoo-module **/
/*
 * This file is used to register the a new button to see all orders data.
 */
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";

class AllOrdersButton extends Component {
static template = 'pos_all_orders.AllOrders';
    setup() {
        this.orm = useService("orm");
        this.pos = usePos();
    }
      async onClick() {
            var session = this.pos.pos_session.id
            var self = this;
           await this.orm.call(
            "pos.session", "get_all_order_config", [], {}
             ).then(function(result){
          if ( result.config == 'current_session'){
                self.orm.call(
            "pos.session", "get_all_order", [{session:session}], {}
             ).then(function(order){
                        self.pos.showScreen('CustomALLOrdrScreen', {
                            orders: order,
                            pos: self.env.pos
                        });
                    });
                }
                else if (result.config == 'past_order'){
                    self.pos.showScreen('CustomALLOrdrScreen', {
                        orders: self.pos.pos_orders,
                        pos: self.env.pos
                    });
                }
                else if (result.config == 'last_n'){
                 self.orm.call(
                "pos.session", "get_all_order", [{session: session, n_days: result.n_days}], {}
                 ).then(function(order){
                        self.pos.showScreen('CustomALLOrdrScreen', {
                            orders: order,
                            pos: self.env.pos
                        });
                    });
                }
                else{
                    self.pos.showScreen('CustomALLOrdrScreen', {
                        orders: self.pos.pos_orders,
                        pos: self.env.pos
                    });
                }
            });
        }
}
ProductScreen.addControlButton({
    component: AllOrdersButton,
    condition: () => true
})
