/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";


patch(ControlButtons.prototype, {
    setup() {
     super.setup(...arguments)
        this.orm = useService("orm");
        this.pos = usePos();

    },
    async onClick() {
          const session = this.pos.config.current_session_id.id
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
                     self.orm.call(
                          "pos.session", "get_all_past_orders", [{session:session}], {}
                           ).then(function(order){
                           self.pos.showScreen('CustomALLOrdrScreen', {
                               orders: order,
                               pos: self.env.pos
                           });
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
                   self.orm.call(
                          "pos.session", "get_default_all_orders", [{session:session}], {}
                           ).then(function(order){
                           self.pos.showScreen('CustomALLOrdrScreen', {
                               orders: order,
                               pos: self.env.pos
                           });
                   });
               }
          });
    }
});