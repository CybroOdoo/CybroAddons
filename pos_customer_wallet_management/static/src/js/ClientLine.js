odoo.define('pos_customer_wallet_management.customerListScreen', function (require) {
    "use strict";

    const ClientLine = require('point_of_sale.ClientLine');
    const Registries = require('point_of_sale.Registries');
    // Extending ClientLine class
    const WalletClientLine = (ClientLine) =>
        class extends ClientLine {
            /**
             *Override PartnerLine
             */
            wallet() {
                //Show wallet recharge screen
                var partner = this.props.partner;
                var data = this.env.pos.payment_methods;
                this.showScreen('RechargeScreen', {
                    result: data,
                    partner: partner,
                });
            }
        }
    Registries.Component.extend(ClientLine, WalletClientLine);
    return ClientLine;
});
