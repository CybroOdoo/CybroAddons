/** @odoo-module **/
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { ConfirmationPopup } from "@simplified_pos/js/ConfirmationPopup";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { useService } from "@web/core/utils/hooks";
import { _lt, _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { CategorySelector } from "@point_of_sale/app/generic_components/category_selector/category_selector";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";



ProductScreen.components = {
 ...ProductScreen.components,
        Numpad,
        PaymentScreenPaymentLines,
        PaymentScreenStatus,
        PaymentScreen,
        OrderWidget,
        CategorySelector,
        ControlButtons,
 };
patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.payment_methods_from_config = this.pos.config.payment_method_ids
        this.pos = usePos();
        this.popup = useService("dialog");
    },
     customerDetails() {
                this.pos.selectPartner();
            },
     confirmOrder() {
                /* When performing validation, this function checks the
                requirements and displays an error message if any are reduced.*/
                var paymentline = this.currentOrder.payment_ids.length
                var partner = this.currentOrder.partner_id
                var orderlines = this.currentOrder.lines.length
                if (orderlines == 0) {
                     this.popup.add(AlertDialog, {
                        title: _t('Error'),
                        body:  _t('Cart is empty.'),
                    });
                }
                else if (partner == null) {
                    this.popup.add(AlertDialog, {
                        title: _t('Error'),
                        body: _t('Select a Customer.'),
                    });
                }
                else if (paymentline == 0) {
                    this.popup.add(AlertDialog, {
                        title: _t('Error'),
                        body: _t('Select a Payment Method'),
                    });
                }
                else {
                    this.popup.add(ConfirmationPopup, {
                        title: _t('Confirmation'),
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
                        this.popup.add(AlertDialog, {
                            title: _t("Error"),
                            body: _t("There is already an electronic payment in progress."),
                        });
                        return false;
                    }
            },
            get paymentLines() {
                return this.currentOrder.payment_ids;
            },

            deletePaymentLine(uuid) {
        const line = this.paymentLines.find((line) => line.uuid === uuid);
        if (line.payment_method_id.payment_method_type === "qr_code") {
            this.currentOrder.remove_paymentline(line);
            this.numberBuffer.reset();
            return;
        }
        // If a paymentline with a payment terminal linked to
        // it is removed, the terminal should get a cancel
        // request.
        if (
            ["waiting", "waitingCard", "timeout"].includes(line.get_payment_status()) &&
            line.payment_method_id.payment_terminal
        ) {
            line.set_payment_status("waitingCancel");
            line.payment_method_id.payment_terminal
                .send_payment_cancel(this.currentOrder, uuid)
                .then(() => {
                    this.currentOrder.remove_paymentline(line);
                    this.numberBuffer.reset();
                });
        } else if (line.get_payment_status() !== "waitingCancel") {
            this.currentOrder.remove_paymentline(line);
            this.numberBuffer.reset();
        }
    },
            get nextScreen() {
                return { name: 'ProductScreen' };
            },

              selectPaymentLine(uuid) {
        const line = this.paymentLines.find((line) => line.uuid === uuid);
        this.currentOrder.select_paymentline(line);
        this.numberBuffer.reset();
    },
              async sendForceDone(line) {
        line.set_payment_status("done");
    },
    async sendPaymentReverse(line) {
        const payment_terminal = line.payment_method_id.payment_terminal;
        line.set_payment_status("reversing");

        const isReversalSuccessful = await payment_terminal.send_payment_reversal(line.uuid);
        if (isReversalSuccessful) {
            line.set_amount(0);
            line.set_payment_status("reversed");
        } else {
            line.can_be_reversed = false;
            line.set_payment_status("done");
        }
    },
    async sendPaymentRequest(line) {
        // Other payment lines can not be reversed anymore
        this.pos.paymentTerminalInProgress = true;
        this.numberBuffer.capture();
        this.paymentLines.forEach(function (line) {
            line.can_be_reversed = false;
        });

        let isPaymentSuccessful = false;
        if (line.payment_method_id.payment_method_type === "qr_code") {
            const resp = await this.pos.showQR(line);
            isPaymentSuccessful = line.handle_payment_response(resp);
        } else {
            isPaymentSuccessful = await line.pay();
        }

        // Automatically validate the order when after an electronic payment,
        // the current order is fully paid and due is zero.
        this.pos.paymentTerminalInProgress = false;
        const config = this.pos.config;
        const currency = this.pos.currency;
        const currentOrder = line.pos_order_id;
        if (
            isPaymentSuccessful &&
            currentOrder.is_paid() &&
            floatIsZero(currentOrder.get_due(), currency.decimal_places) &&
            config.auto_validate_terminal_payment
        ) {
            this.validateOrder(false);
        }
    },
    updateSelectedPaymentline(amount = false) {
        if (this.paymentLines.every((line) => line.paid)) {
            this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
        }
        if (!this.selectedPaymentLine) {
            return;
        } // do nothing if no selected payment line
        if (amount === false) {
            if (this.numberBuffer.get() === null) {
                amount = null;
            } else if (this.numberBuffer.get() === "") {
                amount = 0;
            } else {
                amount = this.numberBuffer.getFloat();
            }
        }
        // disable changing amount on paymentlines with running or done payments on a payment terminal
        const payment_terminal = this.selectedPaymentLine.payment_method_id.payment_terminal;
        const hasCashPaymentMethod = this.payment_methods_from_config.some(
            (method) => method.type === "cash"
        );
        if (
            !hasCashPaymentMethod &&
            amount > this.currentOrder.get_due() + this.selectedPaymentLine.amount
        ) {
            this.selectedPaymentLine.set_amount(0);
            this.numberBuffer.set(this.currentOrder.get_due().toString());
            amount = this.currentOrder.get_due();
            this.showMaxValueError();
        }
        if (
            payment_terminal &&
            !["pending", "retry"].includes(this.selectedPaymentLine.get_payment_status())
        ) {
            return;
        }
        if (amount === null) {
            this.deletePaymentLine(this.selectedPaymentLine.uuid);
        } else {
            this.selectedPaymentLine.set_amount(amount);
        }
    },
    async sendPaymentCancel(line) {
        const payment_terminal = line.payment_method_id.payment_terminal;
        line.set_payment_status("waitingCancel");
        const isCancelSuccessful = await payment_terminal.send_payment_cancel(
            this.currentOrder,
            line.uuid
        );
        if (isCancelSuccessful) {
            line.set_payment_status("retry");
            this.pos.paymentTerminalInProgress = false;
        } else {
            line.set_payment_status("waitingCard");
        }
    }
    })
