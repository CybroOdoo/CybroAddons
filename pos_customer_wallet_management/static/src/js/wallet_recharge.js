odoo.define('pos_customer_wallet_management.wallet_recharge', function(require) {
  'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const PartnerListScreen = require('point_of_sale.PartnerListScreen')
    const { browser } = require("@web/core/browser/browser");
    const { useRef, onMounted } = owl;
    class RechargeScreen extends PosComponent {
        /**
         *Override PosComponent
         */
         setup() {
            super.setup();
            this.amount_input = useRef("amountInput")
            this.journalInput = useRef("journalInput")
            onMounted(() => {
                   this.amount_input.el.value = this.props.amount_input || '';
                   this.journalInput.el.value = this.props.journalInput || '';
            });
        }
        cancel()
        {
            this.showScreen("PartnerListScreen")
        }
        async confirm(partner)
        {
            // Create front end recharge through rpc
            var currency = this.env.pos.currency.name;
            var amount_input = this.amount_input.el.value;
            var journalInput = this.journalInput.el.value;
            if (amount_input.trim() === '' || journalInput.trim() === '') {
                  return;
            }
            var rpc = require('web.rpc');
            rpc.query({
                model: 'recharge.wallet',
                method: 'frontend_recharge',
                args: [partner,amount_input,currency]
            })
            this.showScreen("PartnerListScreen")
             const { confirmed, payload } = await this.showPopup('ConfirmPopup', {
                   title: this.env._t('Confirm Popup'),
                   body: this.env._t('Successfully Recharged Your Wallet'),
             });
             if (confirmed) {
                 browser.location.reload();
             }
        }
    }
    RechargeScreen.template = 'RechargeScreen';
    Registries.Component.add(RechargeScreen);
    return RechargeScreen;
});
