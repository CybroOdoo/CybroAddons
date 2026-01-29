odoo.define('pos_refund_password.RefundPasswordButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const TicketScreen = require('point_of_sale.TicketScreen');
    const rpc = require("web.rpc");

    const PosResTicketScreen1 = (TicketScreen) => class extends TicketScreen {
        async _onDoRefund() {
            let refund = await rpc.query({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ["pos_refund_password.global_refund_security"],
            });

            refund = refund || this.env.pos.config.refund_security;

            if (refund) {
                const { confirmed, payload } = await this.showPopup('NumberPopup');

                if (refund == payload) {
                    super._onDoRefund();
                } else {
                    this.showPopup('ErrorPopup', {
                        body: this.env._t('Invalid Password'),
                    });
                }
            } else {
                super._onDoRefund();
            }
        }
    };

    Registries.Component.extend(TicketScreen, PosResTicketScreen1);
});
