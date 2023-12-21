/** @odoo-module **/
//Extend POS payment screen
  const Registries = require('point_of_sale.Registries');
  const PaymentScreen = require('point_of_sale.PaymentScreen');
  var rpc = require('web.rpc');
  let order_list = []
   const ReferenceButtonPaymentScreen = (PaymentScreen) =>
       class extends PaymentScreen {
        // Click function of add payment reference button.
            async IsPaymentReferenceButton() {
                let { confirmed, payload: code } = await this.showPopup('TextInputPopup', {
                      title: this.env._t('Payment Reference'),
                      startingValue: '',
                      placeholder: this.env._t('eg:PREF16'),
                  });
                if (confirmed) {
                   code = code.trim();
                        if (code !== '') {
                            if (this.env.pos.user_payment_reference.length > 0){
                                this.env.pos.user_payment_reference[this.env.pos.user_payment_reference.length-1].user_payment_reference = code
                                order_list.push({'name':this.env.pos.get_order().name,
                                                 'code': code})
                            }
                            else if (this.env.pos.user_payment_reference.length == 0){
                                this.env.pos.user_payment_reference.user_payment_reference = code
                                order_list.push({'name':this.env.pos.get_order().name,
                                                 'code': code})
                            }
                        }
                }
          }
//          Override the _finalizeValidation() function to write payment
//           reference into that of the pos order
           async _finalizeValidation() {
                await super._finalizeValidation(...arguments);
                rpc.query({
                    model: 'pos.payment',
                    method: 'get_payment_reference',
                    args: [[],order_list],
                });
           }
      };
   Registries.Component.extend(PaymentScreen, ReferenceButtonPaymentScreen);
   return ReferenceButtonPaymentScreen;
