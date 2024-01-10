odoo.define('pos_invoice_payment.InvoicingScreen', function (require) {
    'use strict';
    // Import required modules
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    /* Extending PosComponent to  add Invoicing Screen*/
    class InvoicingScreen extends PosComponent {
        /* super the setup of PosComponent*/
        setup() {
            super.setup();
        }
        /* Function to Navigate back to the ProductScreen */
        back() {
            this.showScreen('ProductScreen');
        }
        /* Function to  Register a payment for the given data_id */
        registerPayment(data_id) {
            var self = this;
            this.rpc({
                model: "account.move",
                method: "register_payment",
                args: [data_id],
            }).then(function (result) {
                /* Function to show ProductScreen*/
                self.showScreen('ProductScreen', {});
            });
        }
        /* Function to confirm the invoice with the given data_id */
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
    };
    /* Template for InvoicingScreen component */
    InvoicingScreen.template = 'InvoicingScreen';
    Registries.Component.add(InvoicingScreen);
    return InvoicingScreen;
});
