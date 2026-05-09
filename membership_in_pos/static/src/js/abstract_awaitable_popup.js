/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import  { Component, reactive } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useState, useRef, onMounted } from "@odoo/owl";

export class MembershipPopup extends Component {
            static template = "membership_in_pos.MembershipPopup";
            static components = { Dialog };
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
                this.dialog = useService("dialog");
                this.state = useState({
                 card : false,
                 productId: false
                 })
                 this.cardCodeRef = useRef("cardCode");
             }
             async Membership_check(){
              var customer_details = []
              const customerInput = this.cardCodeRef.el.value; // Access input value via ref
              this.partner = this.pos.get_order().get_partner()
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
                          this.dialog.add(AlertDialog, {
                                title: _t('Membership'),
                                body: _t('Your Card is Expired/Please check you have membership.')
                          });
                    }
               })
             }
             async confirm() {
                var order    = this.pos.get_order();
                var lines    = order.get_orderlines();
                if (this.state.card){
                   lines.filter((line) => line.get_product() === product).forEach((line) => line.delete());
                  // Add one discount line per tax group
                const linesByTax = order.get_orderlines_grouped_by_tax_ids();
                for (const [tax_ids, lines] of Object.entries(linesByTax)) {
                     // Note that tax_ids_array is an Array of tax_ids that apply to these lines
                      // That is, the use case of products with more than one tax is supported.
                     const tax_ids_array = tax_ids
                        .split(",")
                         .filter((id) => id !== "")
                          .map((id) => Number(id));

                    const baseToDiscount = order.calculate_base_amount(
                        lines.filter((ll) => ll.isGlobalDiscountApplicable())
                    );
                    const taxes = tax_ids_array
                        .map((taxId) => this.pos.models["account.tax"].get(taxId))
                        .filter(Boolean);
                    let discount = - parseFloat(this.state.card.discount) / 100.0 * baseToDiscount;
                    if (discount < 0) {
                      await this.pos.addLineToCurrentOrder(
                            { product_id: this.state.card.product_id, price_unit: discount, tax_ids: [["link", ...taxes]] },
                            { merge: false }
                      );

                    }
                }
                }else{
                var product = 'undefined'
                    this.dialog.add(AlertDialog, {
                      title: _t("No discount product found"),
                      body: _t(
                     "The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."
                    ),
                });
                }
                    this.props.close();
                }
             async cancel() {
             this.props.close();
             }
}
