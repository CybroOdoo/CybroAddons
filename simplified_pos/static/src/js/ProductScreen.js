/** @odoo-module **/
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { ConfirmationPopup } from "@simplified_pos/js/ConfirmationPopup";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { useService } from "@web/core/utils/hooks";
import { _lt, _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

ProductScreen.components = {
 ...ProductScreen.components,
        Numpad,
        PaymentScreenPaymentLines,
        PaymentScreenStatus,
        ProductsWidget,
        Orderline,
        OrderWidget,
 };
patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
         this.payment_methods_from_config = this.pos.payment_methods.filter((method) =>
            this.pos.config.payment_method_ids.includes(method.id)
        );
        this.pos = usePos();
        this.popup = useService("popup");
    },
     customerDetails() {
                this.pos.selectPartner();
            },
     confirmOrder() {
                /* When performing validation, this function checks the
                requirements and displays an error message if any are reduced.*/
                var paymentline = this.currentOrder.paymentlines.length
                var partner = this.currentOrder.partner
                var orderlines = this.currentOrder.orderlines.length
                if (orderlines == 0) {
                     this.pos.env.services.popup.add(ErrorPopup, {
                        title: _t('Error'),
                        body:  _t('Cart is empty.'),
                    });
                }
                else if (partner == null) {
                    this.pos.env.services.popup.add(ErrorPopup, {
                        title: _t('Error'),
                        body: _t('Select a Customer.'),
                    });
                }
                else if (paymentline == 0) {
                    this.pos.env.services.popup.add(ErrorPopup, {
                        title: _t('Error'),
                        body: _t('Select a Payment Method'),
                    });
                }
                else {
                    this.popup.add(ConfirmationPopup, {
                        title: _t('Confirmation'),
                        confirmText: _t('Confirm'),
                        cancelText: _t('Cancel'),
                    });
                }
         },
         orderDone() {
        this.pos.removeOrder(this.currentOrder);
        this._addNewOrder();
        const { name, props } = this.nextScreen;
        this.pos.showScreen(name, props);
    },
     _addNewOrder() {
        this.pos.add_new_order();
    },
            addNewPaymentLine(paymentMethod) {
                const result = this.currentOrder.add_paymentline(paymentMethod);
                    if (result) {
                        this.numberBuffer.reset();
                        return true;
                    } else {
                        this.popup.add(ErrorPopup, {
                            title: _t("Error"),
                            body: _t("There is already an electronic payment in progress."),
                        });
                        return false;
                    }
            },
            get paymentLines() {
                return this.currentOrder.get_paymentlines();
            },
            get_partner() {
                return this.partner;
            },
            set_partner(partner) {
                this.partner = this.env.pos.selectedPartner[4];
            },
             deletePaymentLine(cid) {
                    const lineIndex = this.paymentLines.findIndex((line) => line.cid === cid);
                    if (lineIndex !== -1) {
                        this.paymentLines.splice(lineIndex, 1);
                    }
            },
            get nextScreen() {
                return { name: 'ProductScreen' };
            },
            _selectLine(event) {
                this.currentOrder.select_orderline(event.detail.orderline);
            },
            async sendForceDone(line) {
                line.set_payment_status("done");
            },
            async sendPaymentReverse(line) {
                const payment_terminal = line.payment_method.payment_terminal;
                line.set_payment_status("reversing");

                const isReversalSuccessful = await payment_terminal.send_payment_reversal(line.cid);
                if (isReversalSuccessful) {
                    line.set_amount(0);
                    line.set_payment_status("reversed");
                } else {
                    line.can_be_reversed = false;
                    line.set_payment_status("done");
                }
            }
    })
