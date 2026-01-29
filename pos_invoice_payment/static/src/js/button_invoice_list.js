odoo.define('pos_invoice_payment.invoice_button', function (require) {
    'use strict';
    /**
     * Import required modules.
     */
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    /**
     * Define the InvoicingButton class that extends PosComponent.
     */
    class InvoicingButton extends PosComponent {
        /**
         * This method is called when the component is set up.
         * It sets up event listeners for the 'click' event.
         */
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        /**
         * This method is triggered when the InvoicingButton is clicked.
         * It sends an RPC request to fetch invoices and displays them on the InvoicingScreen.
         */
        async onClick() {
            var self = this;
            await self.rpc({
                model: 'account.move',
                method: 'get_invoices',
            }).then(function (result) {
                self.showScreen('InvoicingScreen', {
                    invoices: result,
                });
            });
        }
    }
    /**
     * Define the template used for the InvoicingButton.
     */
    InvoicingButton.template = 'InvoicingButton';
    /**
     * Add the InvoicingButton as a control button to the ProductScreen.
     * It will be displayed conditionally based on whether 'this.env.pos' is truthy.
     */
    ProductScreen.addControlButton({
        component: InvoicingButton,
        condition: function () {
            return this.env.pos;
        },
    });
    /**
     * Add the InvoicingButton to the list of registered components.
     */
    Registries.Component.add(InvoicingButton);
    /**
     * Export the component name
     */
    return `InvoicingButton`;
});
