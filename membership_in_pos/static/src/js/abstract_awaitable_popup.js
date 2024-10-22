/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Orderline } from "@point_of_sale/app/store/models";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
 //Creates a pop up for membership
export class MembershipPopup extends AbstractAwaitablePopup {
            static template = "membership_in_pos.MembershipPopup";
            static defaultProps = {
                  confirmText: 'Confirm',
                  cancelText: 'Cancel',
                  title: 'Membership Card',
                   body: '',
            };
             setup() {
                super.setup();
                this.pos = usePos();
                this.orm = useService('orm');
                this.state = useState({
                 card : false,
                 productId: false
        })
             }
             async Membership_check(){
             var customer_details = []
             const  customerInput = $('.card_code').val();
             this.partner = this.env.services.pos.get_order().partner
             const customer =  this.partner.id
             customer_details.push({
                  'customerInput':customerInput,
                  'customer':customer
             })
             var self = this
            //This is used to retrieve the customers membership details
             var card = await this.orm.call("membership.card", "membership_card_check", [[]], {customer_input:customer_details}).then((card)=>
             {
                 this.state.card = card
                 if (this.state.card == 0){
                         this.env.services.popup.add(ErrorPopup, {
                                title: _t('Membership'),
                                body: _t('Your Card is Expired/Please check you have membership.')
                         });
                    }
                })
             }
             async confirm() {
                var order    = this.env.services.pos.get_order();
                var lines    = order.get_orderlines();
                if (this.state.card){
                   const products = await this.pos._addProducts([this.state.card.product_id])
                   this.state.productId = order.pos.db.get_product_by_id(this.state.card.product_id)
                }
                else{
                var product  = 'undefined'
                 this.env.services.popup.add(ErrorPopup, {
                    title : _t("No Membership discount product found"),
                    body  : _t("The discount product seems misconfigured.Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'.Also confirm the customer has membership card."),
                 });

               }
                // Remove existing discounts
              lines.filter(line => line.id == product)
              .forEach(line => order.remove_orderline(line))
              let linesByTax = order.get_orderlines_grouped_by_tax_ids();
              for (let [tax_ids, lines] of Object.entries(linesByTax)) {
              let tax_ids_array = tax_ids.split(',').filter(id => id !== '').map(id => Number(id));
               let baseToDiscount = order.calculate_base_amount(tax_ids_array, lines.filter(ll => !ll.reward_id && (!this.env.services.pos.config.tip_product_id || ll.product.id !== this.env.services.pos.config.tip_product_id[0])));
               let discount = - parseFloat(this.state.card.discount) / 100.0 * baseToDiscount;
               if (discount < 0) {
                  var value = await order.add_product(this.state.productId, {
                    price: discount,
                    lst_price: discount,
                    tax_ids: tax_ids_array,
                    merge: false,
                  })

                 }
               }
               this.cancel()
            }
            async cancel(){
                super.cancel();
            }
}
