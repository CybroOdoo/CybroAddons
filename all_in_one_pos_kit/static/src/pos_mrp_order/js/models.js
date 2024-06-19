odoo.define('all_in_one_pos_kit.models_mrp_order', function (require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    //Extends the PaymentScreen to include functionality for creating manufacturing orders from pos.
    const MRPPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        constructor() {
            super(...arguments);
        }
        // Creates a manufacturing order based on the order lines with positive quantities.
        createMRP(){
            const order = this.currentOrder;
            var order_line = order.get_orderlines()
            for (var i in order_line){
                var list_product = []
                if (order_line[i].product){
                    if (order_line[i].quantity>0){
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

                if (list_product.length){
                    rpc.query({
                        model: 'mrp.production',
                        method: 'create_mrp_from_pos',
                        args: [1,list_product],
                    });
                }
            }
        }
        //Validates the order and creates manufacturing orders if applicable. Overrides the existing validateOrder method.
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
                //Remove pending payments before finalizing the validation
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
