odoo.define('pos_invoice_payment.invoice_button', function (require) {
    'use strict';
    // Import required modules
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    /* Extended PosComponent to add invoice buttons functions*/
    class InvoicingButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
       /*Click event handler for InvoicingButton */
        async onClick() {
            var self = this;
           /* Call RPC method to retrieve invoices*/
            await self.rpc({
                model: 'account.move',
                method: 'get_invoices',
            }).then(function (result) {
                /* Show InvoicingScreen with retrieved invoices*/
                self.showScreen('InvoicingScreen', {
                    invoices: result,
                });
            });
        }
    }
    /* Template for InvoicingButton component */
    InvoicingButton.template = 'InvoicingButton';
    ProductScreen.addControlButton({
        component: InvoicingButton,
        /*  The condition function to determine when to show the button*/
        condition: function () {
            return this.env.pos;
        },
    });
    Registries.Component.add(InvoicingButton);
    return `InvoicingButton`;
});
