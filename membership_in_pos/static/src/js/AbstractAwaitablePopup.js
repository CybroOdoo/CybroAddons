odoo.define('membership_in_pos.MembershipPopup', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    var rpc = require('web.rpc');
    //Creates a pop up for membership
    class MembershipPopup extends AbstractAwaitablePopup {
         setup() {
                super.setup();
         }
        // This is used to check the customer has membership
         async Membership_check(){
            var customer_details = []
            const customerInput = $('.card_code').val();
            var order = this.env.pos.get_order()
            var customer = order.get_partner().id
            customer_details.push({
                  'customerInput':customerInput,
                  'customer':customer
            })
            var self = this
            //This is used to retrieve the customers membership details
            var card =  await rpc.query({
                model: 'membership.card',
                method: 'membership_card_check',
                args: [,customer_details]
                }).then(function (card) {
                    self.env.pos.card = card
                    if (self.env.pos.card == 0){
                         Gui.showPopup('ErrorPopup', {
                                title: _t('Membership'),
                                body: _t('Your Card is Expired/Please check you have membership.')
                         });
                    }
                })
         }
         //Confirms the membership
         async confirm() {
            var order    = this.env.pos.get_order();
            var lines    = order.get_orderlines();
            if (this.env.pos.card){
                    var product  = this.env.pos.db.get_product_by_id(this.env.pos.card.product_id);
            }
            else{
                var product  = 'undefined'
                await this.showPopup('ErrorPopup', {
                    title : this.env._t("No Membership discount product found"),
                    body  : this.env._t("The discount product seems misconfigured.Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'.Also confirm the customer has membership card."),
                });
                return;
            }
            // Remove existing discounts
            lines.filter(line => line.get_product() === product)
                .forEach(line => order.remove_orderline(line));
            let linesByTax = order.get_orderlines_grouped_by_tax_ids();
            for (let [tax_ids, lines] of Object.entries(linesByTax)) {
                // Note that tax_ids_array is an Array of tax_ids that apply to these lines
                // That is, the use case of products with more than one tax is supported.
                let tax_ids_array = tax_ids.split(',').filter(id => id !== '').map(id => Number(id));
                let baseToDiscount = order.calculate_base_amount(tax_ids_array, lines.filter(ll => !ll.reward_id && (!this.env.pos.config.tip_product_id || ll.product.id !== this.env.pos.config.tip_product_id[0])));
                // We add the price as manually set to avoid re computation when changing customer.
                let discount = - parseFloat(this.env.pos.card.discount) / 100.0 * baseToDiscount;
                if (discount < 0) {
                    order.add_product(product, {
                        price: discount,
                        lst_price: discount,
                        tax_ids: tax_ids_array,
                        merge: false,
                        description:
                            `${ this.env.pos.card.discount}%, ` +
                            (tax_ids_array.length ?
                                _.str.sprintf(
                                    this.env._t('Tax: %s'),
                                    tax_ids_array.map(taxId => this.env.pos.taxes_by_id[taxId].amount + '%').join(', ')
                                ) :
                            this.env._t('No tax')),
                        extras: {
                            price_automatically_set: true,
                        },
                    });
                }
            }
            this.env.posbus.trigger('close-popup', {
                popupId: this.props.id,
                response: { confirmed: true, payload: null},
            });
         }
	}
    //Create membership popup
    MembershipPopup.template = 'MembershipPopup';
    MembershipPopup.defaultProps = {
    confirmText: 'Ok',
    cancelText: 'Cancel',
    title: 'Membership Card',
    body: '',
   };
   Registries.Component.add(MembershipPopup);
   return MembershipPopup;
});
