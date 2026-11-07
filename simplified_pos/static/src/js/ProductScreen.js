import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Numpad } from "@point_of_sale/app/components/numpad/numpad";
import { ConfirmationPopup } from "@simplified_pos/js/ConfirmationPopup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { CategorySelector } from "@point_of_sale/app/components/category_selector/category_selector";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

Object.assign(ProductScreen.components, {
    Numpad,
    PaymentScreenPaymentLines,
    PaymentScreenStatus,
    PaymentScreen,
    CategorySelector,
    ControlButtons,
});

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.popup = this.dialog;
    },
    get payment_methods_from_config() {
        return this.pos.config.paymentMethods || [];
    },
    customerDetails() {
        this.pos.selectPartner();
    },
    confirmOrder() {
        /* When performing validation, this function checks the
        requirements and displays an error message if any are reduced.*/
        var paymentline = this.currentOrder?.payment_ids?.length || 0;
        var partner = this.currentOrder?.partner_id || this.currentOrder?.getPartner();
        var orderlines = this.currentOrder?.lines?.length || 0;
        if (orderlines === 0) {
            this.dialog.add(AlertDialog, {
                title: _t('Error'),
                body: _t('Cart is empty.'),
            });
        }
        else if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t('Error'),
                body: _t('Select a Customer.'),
            });
        }
        else if (paymentline === 0) {
            this.dialog.add(AlertDialog, {
                title: _t('Error'),
                body: _t('Select a Payment Method'),
            });
        }
        else {
            this.dialog.add(ConfirmationPopup, {
                title: _t('Confirmation'),
            });
        }
    },
    orderDone() {
        this._addNewOrder();
    },
    _addNewOrder() {
        this.pos.addNewOrder();
    },
    addNewPaymentLine(paymentMethod) {
        const result = this.currentOrder?.addPaymentline(paymentMethod);
        if (result) {
            this.numberBuffer.reset();
            return true;
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("There is already an electronic payment in progress."),
            });
            return false;
        }
    },
    get paymentLines() {
        return this.currentOrder?.payment_ids || [];
    },
    get isRefundOrder() {
        return Boolean(this.currentOrder?.isRefund);
    },
    deletePaymentLine(uuid) {
        const line = this.paymentLines.find((line) => line.uuid === uuid);
        if (!line) {
            return;
        }
        if (line.payment_method_id?.payment_method_type === "qr_code") {
            this.currentOrder.removePaymentline(line);
            this.numberBuffer.reset();
            return;
        }
        if (
            ["waiting", "waitingCard", "timeout"].includes(line.getPaymentStatus()) &&
            line.payment_method_id?.payment_terminal
        ) {
            line.set_payment_status("waitingCancel");
            line.payment_method_id.payment_terminal
                .send_payment_cancel(this.currentOrder, uuid)
                .then(() => {
                    this.currentOrder.removePaymentline(line);
                    this.numberBuffer.reset();
                });
        } else if (line.getPaymentStatus() !== "waitingCancel") {
            this.currentOrder.removePaymentline(line);
            this.numberBuffer.reset();
        }
    },
    selectPaymentLine(uuid) {
        const line = this.paymentLines.find((line) => line.uuid === uuid);
        if (line) {
            this.currentOrder.selected_paymentline = line;
            this.numberBuffer.reset();
        }
    },
    async sendForceDone(line) {
        line?.set_payment_status("done");
    },
    async sendForceCancel(line) {
        line?.forceCancel();
    },
    async sendPaymentReverse(line) {
        const payment_terminal = line.payment_method_id?.payment_terminal;
        if (!payment_terminal) {
            return;
        }
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
        this.pos.paymentTerminalInProgress = true;
        this.numberBuffer.capture();
        this.paymentLines.forEach(function (line) {
            line.can_be_reversed = false;
        });

        let isPaymentSuccessful = false;
        if (line.payment_method_id?.payment_method_type === "qr_code") {
            const resp = await this.pos.showQR(line);
            isPaymentSuccessful = line.handle_payment_response(resp);
        } else {
            isPaymentSuccessful = await line.pay();
        }

        this.pos.paymentTerminalInProgress = false;
        const config = this.pos.config;
        const currency = this.pos.currency;
        const currentOrder = line.pos_order_id;
        if (
            isPaymentSuccessful &&
            currentOrder?.is_paid() &&
            config.auto_validate_terminal_payment
        ) {
            this.validateOrder(false);
        }
    },
    updateSelectedPaymentline(amount = false) {
        if (this.paymentLines.every((line) => line.paid) && this.payment_methods_from_config.length > 0) {
            this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
        }
        if (!this.selectedPaymentLine) {
            return;
        }
        if (amount === false) {
            if (this.numberBuffer.get() === null) {
                amount = null;
            } else if (this.numberBuffer.get() === "") {
                amount = 0;
            } else {
                amount = this.numberBuffer.getFloat();
            }
        }
        const payment_terminal = this.selectedPaymentLine.payment_method_id?.payment_terminal;
        const hasCashPaymentMethod = this.payment_methods_from_config.some(
            (method) => method.type === "cash"
        );
        if (
            !hasCashPaymentMethod &&
            amount > (this.currentOrder?.get_due() || 0) + this.selectedPaymentLine.amount
        ) {
            this.selectedPaymentLine.set_amount(0);
            this.numberBuffer.set((this.currentOrder?.get_due() || 0).toString());
            amount = this.currentOrder?.get_due() || 0;
            if (this.showMaxValueError) {
                this.showMaxValueError();
            }
        }
        if (
            payment_terminal &&
            !["pending", "retry"].includes(this.selectedPaymentLine.getPaymentStatus())
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
        const payment_terminal = line.payment_method_id?.payment_terminal;
        if (!payment_terminal) {
            return;
        }
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
});

