import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export function useSalonBookingActions({ onChange } = {}) {
    const pos = usePos();
    const orm = useService("orm");
    const dialog = useService("dialog");

    const state = useState({
        showCommissionPopup: false,
        commissionBooking: null,
        commissionAmount: "",
        commissionWarning: "",
    });

    const showError = (title, err, fallback) => {
        dialog.add(AlertDialog, {
            title,
            body: err?.data?.message || err?.message || fallback,
        });
    };

    const actions = {
        state,

        payBooking(appt) {
            const config = pos.config;
            const needsAmount =
                config.apply_commission &&
                config.commission_type === "manual" &&
                appt.specialist_name;
            if (!needsAmount) {
                return actions.openPayment(appt);
            }
            const suggested = ((appt.amount_total || 0) * (config.commission_percent || 0)) / 100;
            state.commissionBooking = appt;
            state.commissionAmount = suggested ? String(Number(suggested.toFixed(2))) : "";
            state.commissionWarning = "";
            state.showCommissionPopup = true;
        },

        setCommissionAmount(value) {
            state.commissionAmount = value;
        },

        closeCommissionPopup() {
            state.showCommissionPopup = false;
        },

        async confirmCommission() {
            const amount = parseFloat(state.commissionAmount);
            if (!amount || amount <= 0) {
                state.commissionWarning = _t("Please add the commission amount. It cannot be 0.");
                return;
            }
            const appt = state.commissionBooking;
            state.showCommissionPopup = false;
            await actions.openPayment(appt, amount);
        },

        async openPayment(appt, commissionAmount = 0) {
            try {
                const data = await orm.call(
                    "salon.booking", "action_prepare_payment", [[appt.id]],
                    { commission_amount: commissionAmount }
                );
                let order = pos.models["pos.order"].find(
                    (o) => o.state === "draft" && o.salon_booking_ref === appt.id
                );
                if (!order) {
                    const models = pos.models;
                    const partner =
                        models["res.partner"].get(data.partner_id) ||
                        (await pos.data.read("res.partner", [data.partner_id]))[0];
                    const template =
                        models["product.template"].get(data.product_tmpl_id) ||
                        (await pos.data.read("product.template", [data.product_tmpl_id]))[0];
                    order = pos.addNewOrder({
                        partner_id: partner,
                        salon_booking_ref: appt.id,
                    });
                    for (const line of data.lines) {
                        const added = await pos.addLineToOrder(
                            {
                                product_tmpl_id: template,
                                full_product_name: line.name,
                                price_unit: line.price,
                                qty: 1,
                            },
                            order, {}, false
                        );
                        const posLine = added || order.lines[order.lines.length - 1];
                        if (posLine) {
                            posLine.full_product_name = line.name;
                        }
                    }
                }
                pos.navigate("PaymentScreen", { orderUuid: order.uuid });
            } catch (err) {
                showError(_t("Payment"), err, _t("Could not open the payment screen"));
            }
        },

        formatAmount(value) {
            return formatSalonAmount(pos, value);
        },

        paymentLabel(paymentState) {
            return { unpaid: _t("Unpaid"), partial: _t("Partially Paid"), paid: _t("Paid") }[paymentState] || _t("Unpaid");
        },

        stateLabel(bookingState) {
            return {
                draft: _t("Draft"), confirmed: _t("Confirmed"), done: _t("Completed"),
                cancelled: _t("Cancelled"), rescheduled: _t("Rescheduled"),
            }[bookingState] || _t("Unknown");
        },

        canPay(appt) {
            return ["confirmed", "done"].includes(appt.state) && appt.payment_state !== "paid";
        },

        canComplete(appt) {
            return appt.state === "confirmed";
        },

        canCancel(appt) {
            return appt.state === "confirmed" && appt.payment_state === "unpaid";
        },

        async completeBooking(appt) {
            try {
                await orm.call("salon.booking", "action_done", [[appt.id]]);
                if (onChange) {
                    await onChange();
                }
            } catch (err) {
                showError(_t("Complete appointment"), err, _t("Could not complete the booking"));
            }
        },

        async markArrived(appt) {
            try {
                await orm.call("salon.booking", "action_mark_arrived", [[appt.id]]);
                if (onChange) {
                    await onChange();
                }
            } catch (err) {
                showError(_t("Arrived"), err, _t("Could not mark the customer as arrived"));
            }
        },

        cancelBooking(appt) {
            dialog.add(ConfirmationDialog, {
                title: _t("Cancel appointment"),
                body: _t("Cancel the appointment for %s?", appt.customer_name),
                confirmLabel: _t("Yes, cancel it"),
                cancelLabel: _t("Keep"),
                confirm: async () => {
                    try {
                        await orm.call("salon.booking", "action_cancel", [[appt.id]]);
                        if (onChange) {
                            await onChange();
                        }
                    } catch (err) {
                        showError(_t("Cancel appointment"), err, _t("Could not cancel the booking"));
                    }
                },
            });
        },
    };

    return actions;
}