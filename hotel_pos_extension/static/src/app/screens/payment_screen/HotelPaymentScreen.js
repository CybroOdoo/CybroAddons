/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    _getPaymentMethodsForLookup() {
        return this.payment_methods_from_config || [];
    },

    get currentOrder() {
        return this.pos.models["pos.order"].getBy("uuid", this.props.orderUuid);
    },

    getHotelChargePaymentMethod() {
        return this.payment_methods_from_config.find((m) => {
            const loaded = this.pos.models["pos.payment.method"].get(m.id);
            return m.is_hotel_charge || loaded?.is_hotel_charge;
        });
    },

    async addNewPaymentLine(paymentMethod) {
        const order = this.currentOrder;
        const loaded = paymentMethod?.id
            ? this.pos.models["pos.payment.method"].get(paymentMethod.id)
            : null;
        const isHotelCharge = paymentMethod?.is_hotel_charge || loaded?.is_hotel_charge;
        if (isHotelCharge) {
            if (!order.getBookingId()) {
                this.dialog.add(AlertDialog, {
                    title: _t("Please select the Room"),
                    body: _t("Select a room booking before using Pay at Checkout."),
                });
                return false;
            }
            if (!order.partner_id) {
                this.dialog.add(AlertDialog, {
                    title: _t("Customer Required"),
                    body: _t("Please select a customer before using the hotel charge payment method as an invoice will be created."),
                });
                return false;
            }
            if (!order.isToInvoice()) {
                const confirmed = await new Promise((resolve) => {
                    this.dialog.add(ConfirmationDialog, {
                        title: _t("Invoice required"),
                        body: _t(
                            "Enable invoicing for this order to use the hotel charge payment method?"
                        ),
                        confirm: () => {
                            order.setToInvoice(true);
                            resolve(true);
                        },
                        cancel: () => resolve(false),
                    });
                });
                if (!confirmed) {
                    return false;
                }
            }
        }
        return await super.addNewPaymentLine(paymentMethod);
    },

    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        const hotel_payments = (order?.payment_ids || []).filter((line) => {
            const method = this.pos.models["pos.payment.method"].get(line.payment_method_id.id || line.payment_method_id);
            return method?.is_hotel_charge;
        });

        if (hotel_payments.length > 0 && !order.getBookingId()) {
            const confirmed = await new Promise((resolve) => {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Please select the Room"),
                    body: _t("You need to select a hotel room booking before using Pay at Checkout."),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });
            if (!confirmed) {
                return;
            }
            return;
        }

        if (hotel_payments.length > 0 && !order.isToInvoice()) {
            const confirmed = await new Promise((resolve) => {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Please select the Invoice"),
                    body: _t("You need to select the invoice before using Pay at Checkout."),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });
            if (!confirmed) {
                return;
            }
            return;
        }

        return await super.validateOrder(isForceValidate);
    }
});
