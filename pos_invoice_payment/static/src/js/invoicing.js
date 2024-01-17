odoo.define('pos_invoice_payment.InvoicingScreen', function (require) {
    'use strict';
    /**
     * Import required modules.
     */
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    var core = require('web.core');
    const { onMounted, onWillUnmount, useState } = owl;
    /**
     * Define the InvoicingScreen class that extends PosComponent.
     */
    class InvoicingScreen extends PosComponent {
        /**
         * This method is called when the component is set up.
         * It can be used to perform setup tasks.
         */
        setup() {
            super.setup();
        }
        /**
         * This method is called when the 'back' button is clicked.
         * It navigates back to the ProductScreen.
         */
        back() {
            this.showScreen('ProductScreen');
        }
        /**
         * This method is called when the 'register payment' button is clicked.
         * It sends an RPC request to register a payment for the selected data_id (invoice).
         * After successful registration, it navigates back to the ProductScreen.
         * @param {integer} data_id - The ID of the invoice to register payment for.
         */
        registerPayment(data_id) {
            var self = this;
            this.rpc({
                model: "account.move",
                method: "register_payment",
                args: [data_id],
            }).then(function (result) {
                self.showScreen('ProductScreen', {});
            });
        }
        /**
         * This method is called when the 'Confirm' button is clicked.
         * It sends an RPC request to post the invoice for the selected data_id.
         * After successful confirmation, it navigates back to the ProductScreen.
         * @param {integer} data_id - The ID of the invoice to confirm.
         */
        Confirm(data_id) {
            var self = this;
            this.rpc({
                model: "account.move",
                method: "post_invoice",
                args: [data_id],
            }).then(function (result) {
                self.showScreen('ProductScreen', {});
            });
        }
    }
    /**
     * Define the template used for the InvoicingScreen.
     */
    InvoicingScreen.template = 'InvoicingScreen';
    /**
     * Add the InvoicingScreen to the list of registered components.
     */
    Registries.Component.add(InvoicingScreen);
    /**
     * Export the InvoicingScreen class.
     */
    return InvoicingScreen;
});
