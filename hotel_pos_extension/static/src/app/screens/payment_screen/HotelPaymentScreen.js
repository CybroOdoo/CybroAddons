/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    _getPaymentMethodsForLookup() {
        return this.payment_methods_from_config || [];
    },

    getHotelChargePaymentMethod() {
        return this.payment_methods_from_config.find((m) => {
            const loaded = this.pos.payment_methods_by_id[m.id];
            return m.is_hotel_charge || loaded?.is_hotel_charge;
        });
    },

    async addNewPaymentLine(paymentMethod) {
        const order = this.currentOrder;
        const loaded = paymentMethod?.id
            ? this.pos.payment_methods_by_id[paymentMethod.id]
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
            if (!order.get_partner()) {
                this.dialog.add(AlertDialog, {
                    title: _t("Customer Required"),
                    body: _t("Please select a customer before using the hotel charge payment method as an invoice will be created."),
                });
                return false;
            }
            if (!order.is_to_invoice()) {
                const confirmed = await new Promise((resolve) => {
                    this.dialog.add(ConfirmationDialog, {
                        title: _t("Invoice required"),
                        body: _t(
                            "Enable invoicing for this order to use the hotel charge payment method?"
                        ),
                        confirm: () => {
                            order.set_to_invoice(true);
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
        const hotel_payments = (order.get_paymentlines() || []).filter((line) => {
            const method = line.payment_method?.id ? this.pos.payment_methods_by_id[line.payment_method.id] : line.payment_method;
            return line.payment_method?.is_hotel_charge || method?.is_hotel_charge;
        });

        if (hotel_payments.length > 0 && !order.getBookingId()) {
            this.dialog.add(AlertDialog, {
                title: _t("Please select the Room"),
                body: _t("You need to select a hotel room booking before using Pay at Checkout."),
            });
            return false;
        }

        if (hotel_payments.length > 0 && !order.is_to_invoice()) {
            this.dialog.add(AlertDialog, {
                title: _t("Please select the Invoice"),
                body: _t("You need to select the invoice before using Pay at Checkout."),
            });
            return false;
        }

        return await super.validateOrder(isForceValidate);
    }
});
