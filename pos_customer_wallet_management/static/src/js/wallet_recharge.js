/** @odoo-module */
import { Component } from "@odoo/owl";
import { browser } from "@web/core/browser/browser"
import { useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { _t } from "@web/core/l10n/translation";

export class RechargeScreen extends Component {
                static template = "pos_customer_wallet_management.RechargeScreen";

                static defaultProps = {
                  confirmText: 'Add',
                  cancelText: 'Cancel',
                  title: 'Wallet Recharge',
                   body: '',
            };
           setup() {
                this.amount_input = useRef("amountInput");
                this.journalInput = useRef("journalInput");
                this.orm = useService('orm');
            onMounted(() => {
                this.amount_input.el.value = this.props.amount_input || '';
                this.journalInput.el.value = this.props.journalInput || '';
            });
           }
      async confirm() {
             var partner = this.props.partner
             var currency = this.env.services.pos.currency.name;
             var session = this.env.services.pos.pos_session.name
             var amount_input = this.amount_input.el.value;
             var journalInput = this.journalInput.el.value;
             if (amount_input.trim() === '' || journalInput.trim() === '') {
                return;
             }
             const rpc = await this.orm.call("recharge.wallet", "frontend_recharge", [partner, amount_input, currency, session]);
             const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                    title: _t('Confirm Popup'),
                    body: _t('Successfully Recharged Your Wallet'),
                    confirmText: _t("Ok"),
             });
             if (confirmed) {
                   browser.location.reload();
             }
      }
      cancel() {
            browser.location.reload();
      }
}

