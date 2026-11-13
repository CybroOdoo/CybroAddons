import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class TrackAllAppointmentsScreen extends Component {
    static template = "pos_salon.TrackAllAppointmentsScreen";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            appointments: [],
            loading: true,
            error: null,
            showCommissionPopup: false,
            commissionBooking: null,
            commissionAmount: '',
            commissionWarning: '',
        });

        this.loadAllAppointments();
    }

    async loadAllAppointments() {
        this.state.loading = true;
        this.state.error = null;
        try {
            this.state.appointments = await this.orm.searchRead(
                "salon.booking",
                [],
                ["customer_name", "customer_phone", "date", "slot", "time_period", "service_name", "state", "payment_state", "specialist_name", "amenity_names", "amount_total", "amount_payable", "amount_due", "commission_amount", "rating", "review_mail_sent", "customer_email"],
                { order: "date desc, id desc" }
            );
        } catch (err) {
            this.state.error = err.data?.message || err.message || _t("Network error");
            this.state.appointments = [];
        } finally {
            this.state.loading = false;
        }
    }

    stateLabel(state) {
        return { draft: 'Draft', confirmed: 'Confirmed', done: 'Completed', cancelled: 'Cancelled', rescheduled: 'Rescheduled' }[state] || 'Unknown';
    }

    formatAmount(value) {
        return formatSalonAmount(this.pos, value);
    }

    paymentLabel(paymentState) {
        return { unpaid: 'Unpaid', partial: 'Partially Paid', paid: 'Paid' }[paymentState] || 'Unpaid';
    }

    async changeState(id, action, kwargs = {}) {
        try {
            await this.orm.call("salon.booking", action, [[id]], kwargs);
            await this.loadAllAppointments();
        } catch (err) {
            this.state.error = err.data?.message || err.message || _t("Could not update booking");
        }
    }

    payBooking(appt) {
        const config = this.pos.config;
        const needsAmount = config.apply_commission
            && config.commission_type === 'manual'
            && appt.specialist_name;
        if (!needsAmount) {
            return this.openPayment(appt);
        }
        const suggested = (appt.amount_total || 0) * (config.commission_percent || 0) / 100;
        this.state.commissionBooking = appt;
        this.state.commissionAmount = suggested ? String(Number(suggested.toFixed(2))) : '';
        this.state.commissionWarning = '';
        this.state.showCommissionPopup = true;
    }

    closeCommissionPopup() {
        this.state.showCommissionPopup = false;
    }

    async confirmCommission() {
        const amount = parseFloat(this.state.commissionAmount);
        if (!amount || amount <= 0) {
            this.state.commissionWarning = "Please add the commission amount. It cannot be 0.";
            return;
        }
        const appt = this.state.commissionBooking;
        this.state.showCommissionPopup = false;
        await this.openPayment(appt, amount);
    }

    async openPayment(appt, commissionAmount = 0) {
        try {
            const data = await this.orm.call(
                "salon.booking", "action_prepare_payment", [[appt.id]],
                { commission_amount: commissionAmount }
            );
            let order = this.pos.models["pos.order"].find(
                (o) => o.state === "draft" && o.salon_booking_ref === appt.id
            );
            if (!order) {
                const models = this.pos.models;
                const partner = models["res.partner"].get(data.partner_id)
                    || (await this.pos.data.read("res.partner", [data.partner_id]))[0];
                const template = models["product.template"].get(data.product_tmpl_id)
                    || (await this.pos.data.read("product.template", [data.product_tmpl_id]))[0];
                order = this.pos.addNewOrder({
                    partner_id: partner,
                    salon_booking_ref: appt.id,
                });
                for (const line of data.lines) {
                    const added = await this.pos.addLineToOrder({
                        product_tmpl_id: template,
                        full_product_name: line.name,
                        price_unit: line.price,
                        qty: 1,
                    }, order, {}, false);
                    const posLine = added || order.lines[order.lines.length - 1];
                    if (posLine) {
                        posLine.full_product_name = line.name;
                    }
                }
            }
            this.pos.navigate("PaymentScreen", { orderUuid: order.uuid });
        } catch (err) {
            this.dialog.add(AlertDialog, {
                title: _t("Payment"),
                body: err.data?.message || err.message || _t("Could not open the payment screen"),
            });
        }
    }

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    formatSlot(slotStr) {
        if (!slotStr) return '-';
        if (slotStr === 'Walk-in') return 'Walk-in';

        try {
            const slotData = JSON.parse(slotStr);
            const firstServiceSlots = Object.values(slotData)[0];
            if (firstServiceSlots && firstServiceSlots.length > 0) {
                return firstServiceSlots.join(", ");
            }
            return 'Scheduled';
        } catch (e) {
            return slotStr;
        }
    }

    back() {
        this.pos.router.navigate("SalonScreen");
    }

    refresh() {
        this.loadAllAppointments();
    }
}

registry.category("pos_pages").add("TrackAllAppointmentsScreen", {
    name: "TrackAllAppointmentsScreen",
    component: TrackAllAppointmentsScreen,
    route: `/pos/ui/${odoo.pos_config_id}/track-all-appointments`,
});
