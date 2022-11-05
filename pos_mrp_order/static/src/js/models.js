odoo.define('pos_mrp_order.models_mrp_order', function (require) {
"use strict";
var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');

    const MRPPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            createMRP(){
                const order = this.currentOrder;
            var order_line = order.get_orderlines()
            var due = order.get_due();
             for (var i in order_line)
              {
		         var list_product = []
                 if (order_line[i].product)
                 {

                   if (order_line[i].quantity>0)
                   {
                     var product_dict = {
                        'id': order_line[i].product.id,
                        'qty': order_line[i].quantity,
                        'product_tmpl_id': order_line[i].product.product_tmpl_id,
                        'pos_reference': order.name,
                        'uom_id': order_line[i].product.uom_id[0],
                   };
                  list_product.push(product_dict);
                 }

              }

              if (list_product.length)
              {
                rpc.query({
                    model: 'mrp.production',
                    method: 'create_mrp_from_pos',
                    args: [1,list_product],
                    });
              }
            }
            }
            async validateOrder(isForceValidate) {
            if(this.env.pos.config.cash_rounding) {
                if(!this.env.pos.get_order().check_paymentlines_rounding()) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Rounding error in payment lines'),
                        body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                    });
                    return;
                }
            }
            if (await this._isOrderValid(isForceValidate)) {
                // remove pending payments before finalizing the validation
                for (let line of this.paymentLines) {
                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                }
                await this._finalizeValidation();
            }
            this.createMRP();
        }
        };

    Registries.Component.extend(PaymentScreen, MRPPaymentScreen);

    return MRPPaymentScreen;

});
