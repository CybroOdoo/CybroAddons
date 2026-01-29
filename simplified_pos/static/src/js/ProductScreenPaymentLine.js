odoo.define('simplified_pos.ProductScreenPaymentLine', function(require) {
    'use strict';
    const PaymentScreenPaymentLines = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const {
        useListener
    } = require("@web/core/utils/hooks");
    const ProductScreenPaymentLine = (PaymentScreenPaymentLines) =>
        class extends PaymentScreenPaymentLines {
            /*Here  PaymentScreenPaymentLines is extended.*/
            setup() {
                super.setup();
                useListener('delete-payment', this.deletePayment);
                useListener('select-payment-line', this.selectPaymentLine);
            }
            selectPaymentLine(event) {
                /*This helps to select payment line in summary.*/
                const {
                    cid
                } = event.detail;
                const line = this.env.pos.get_order().get_paymentlines().find((line) => line.cid === cid);
                this.env.pos.get_order().select_paymentline(line);
                NumberBuffer.reset();
                this.render(true);
            }
            deletePayment(event) {
                /*This is to delete payment lines from summary.*/
                const {
                    cid
                } = event.detail;
                const paymentline = this.env.pos.get_order().get_paymentlines().find((line) => line.cid === cid)
                if (paymentline) {
                    this.env.pos.get_order().remove_paymentline(paymentline)
                    this.render(true)
                }
            }
        };
    Registries.Component.extend(PaymentScreenPaymentLines, ProductScreenPaymentLine);
    return ProductScreenPaymentLine;
});