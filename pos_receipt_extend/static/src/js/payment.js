odoo.define('pos_receipt_extend.PaymentScreen', function (require) {
    'use strict';
    var rpc = require('web.rpc')
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
        // Load models to retrieve configuration and account move data
        // Load 'pos.config' model fields
    models.load_models([{
        model: 'pos.config',
        fields: ['is_customer_details', 'is_customer_name', 'is_customer_address', 'is_customer_mobile', 'is_customer_phone', 'is_customer_email', 'is_customer_vat', 'is_qr_code', 'is_invoice_number'],
        loaded: function (self, pos_config) {
            self.pos_config = pos_config;
        }
    }]);
       // Load 'account.move' model fields
    models.load_models([{
        model: 'account.move',
        fields: ['name'],
        loaded: function (self, account_move) {
            self.account_move = account_move;
        }
    }]);
        // Define the extended PaymentScreen component
    const PosPaymentReceiptExtend = PaymentScreen => class extends PaymentScreen {
        setup() {
            super.setup();
        }
        async validateOrder(isForceValidate) {
            // Retrieve receipt number from the selected order
            var receipt_number = this.env.pos._previousAttributes.selectedOrder.name
            const receipt_order = await super.validateOrder(...arguments);
             // Generate QR code and store it
            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
            var self = this;
            rpc.query({
                model: 'pos.order',
                method: 'get_invoice',
                args: [receipt_number]
            }).then(function (result) {
                self.env.pos.inv = result['invoice_name']
                const address = `${result.base_url}/my/invoices/${result.invoice_id}?`
                let qr_code_svg = new XMLSerializer().serializeToString(codeWriter.write(address, 150, 150));
                self.env.pos.qr_image = "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
            });
            return receipt_order
        }
    }
        // Extend the PaymentScreen component with the custom functionality
    Registries.Component.extend(PaymentScreen, PosPaymentReceiptExtend);
    return PaymentScreen;
});
