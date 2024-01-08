odoo.define('pos_receipt_extend.PaymentScreen', function (require) {
    'use strict';
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');
    const { onMounted } = owl;
    const { Gui } = require('point_of_sale.Gui');
    const PosPaymentReceiptExtend = PaymentScreen =>
        class extends PaymentScreen {
         /**
         * Validates the order and performs customization for the receipt.
         * @param {boolean} isForceValidate - Whether to forcefully validate the order.
         */
            async validateOrder(isForceValidate) {
                await super.validateOrder(...arguments);
                const selectedOrder = this.env.pos.get_order();
                const receiptNumber = selectedOrder.name;
                const order = this.env.pos.config;
                const {
                    is_customer_mobile,
                    is_customer_phone,
                    is_customer_email,
                    is_customer_vat,
                    is_customer_address,
                    is_customer_name,
                    is_invoice_number,
                    is_qr_code,
                } = order;
                const customer = selectedOrder.get_client();
                if (!is_customer_address) customer.street = null;
                if (!is_customer_name) customer.name = null;
                if (!is_customer_mobile) customer.mobile = null;
                if (!is_customer_phone) customer.phone = null;
                if (!is_customer_email) customer.email = null;
                if (!is_customer_vat) customer.vat = null;
                if (!is_invoice_number) selectedOrder.name = null;
                if (is_qr_code || is_invoice_number) {
                    const result = await rpc.query({
                        model: 'pos.order',
                        method: 'get_invoice',
                        args: [receiptNumber],
                    });
                    if (is_qr_code) {
                        const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
                        const address = `${result.base_url}/my/invoices/${result.invoice_id}?`;
                        const qrCodeSvg = new XMLSerializer().serializeToString(
                            codeWriter.write(address, 150, 150)
                        );
                        this.env.pos.qr_image = `data:image/svg+xml;base64,${window.btoa(qrCodeSvg)}`;
                    }
                    if (is_invoice_number) {
                        this.env.pos.invoice = result.invoice_name;
                    }
                    this.refreshReceipt()
                }
            }
            /**
             * Refreshes the receipt and prompts the user to display it on the customer screen.
             */
            refreshReceipt() {
                Gui.showPopup('ConfirmPopup', {
                    title: 'Do you want to display receipt in customer screen',
                    confirmText: 'To Customer screen',  // Add the confirm button text
                    confirm: this.env.pos.send_current_order_to_customer_facing_display(),  // Call printReceipt when confirm is clicked
                });
            }
        };
    Registries.Component.extend(PaymentScreen, PosPaymentReceiptExtend);
    return PaymentScreen;
});
