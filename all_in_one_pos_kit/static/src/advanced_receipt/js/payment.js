odoo.define('all_in_one_pos_kit.PaymentScreen', function(require) {
    'use strict';
    var rpc = require('web.rpc')
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const PosPaymentReceiptExtend = PaymentScreen => class extends PaymentScreen {
        //Extends the PaymentScreen component to add custom functionality.
        setup() {
            //Performs setup operations for the extended component.
            super.setup();
        }
        async validateOrder(isForceValidate) {
            //Validates the order and performs additional checks if customer details are required.
            if (this.env.pos.res_config_settings[this.env.pos.res_config_settings.length - 1].customer_details == true && !this.currentOrder.get_partner()) {
                const {
                    confirmed
                } = await this.showPopup('ConfirmPopup', {
                    title: ('Customer Required')
                });
                if (confirmed) {
                    this.selectPartner();
                }
                return false;
            }
            const receipt_order = await super.validateOrder(...arguments); // Call the original validateOrder() method
            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter(); // Generate QR code and retrieve additional information from the server
            var self = this;
            rpc.query({
                model: 'pos.order',
                method: 'get_invoice',
                args: [this.env.pos.selectedOrder.name]
            }).then(function(result) {
                const address = `${result.base_url}/my/invoices/${result.invoice_id}?`
                let qr_code_svg = new XMLSerializer().serializeToString(codeWriter.write(address, 150, 150));
                self.env.pos.qr_image = "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
                let barcode_svg = new XMLSerializer().serializeToString(codeWriter.write(result.barcode, 150, 150));
                self.env.pos.barcode_image = "data:image/svg+xml;base64," + window.btoa(barcode_svg);
                self.env.pos.barcode = result.barcode
                self.env.pos.invoice = result.invoice_name
            });
            return receipt_order
        }
    }
    Registries.Component.extend(PaymentScreen, PosPaymentReceiptExtend); // Extend the PaymentScreen component with the custom functionality
    return PaymentScreen;
});
