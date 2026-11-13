import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useSalonBookingActions } from "@pos_salon/app/hooks/salon_booking_actions";
import { SalonCommissionPopup } from "@pos_salon/app/components/salon_commission_popup/salon_commission_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { getLocalToday } from "@pos_salon/app/utils/salon_date";

export class WalkInAppointmentsScreen extends Component {
    static template = "pos_salon.WalkInAppointmentsScreen";
    static components = { SalonCommissionPopup };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.actions = useSalonBookingActions({ onChange: () => this.loadAppointments() });
        this.state = useState({
            appointments: [],
            loading: true,
            error: null
        });

        this.loadAppointments();
    }

    async loadAppointments() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const today = getLocalToday();
            const result = await this.orm.searchRead(
                "salon.booking",
                [
                    "|",
                    ["state", "=", "confirmed"],
                    "&",
                    ["state", "=", "done"],
                    ["payment_state", "!=", "paid"],
                    ["date", "=", today],
                ],
                ["customer_name", "customer_phone", "date", "slot", "time_period", "checked_in", "service_name", "state", "payment_state", "specialist_name", "amenity_names", "amount_total", "amount_payable", "amount_due"],
                { order: "date desc, id desc" }
            );
            this.state.appointments = result.filter(appt => {
                const slot = appt.slot || '';
                return slot.trim() === 'Walk-in';
            });
        } catch (err) {
            this.state.error = err.data?.message || err.message || _t("Network error");
            this.state.appointments = [];
        } finally {
            this.state.loading = false;
        }
    }


    refresh() {
        this.loadAppointments();
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
}

registry.category("pos_pages").add("WalkInAppointmentsScreen", {
    name: "WalkInAppointmentsScreen",
    component: WalkInAppointmentsScreen,
    route: `/pos/ui/${odoo.pos_config_id}/walk-in-screen`,
});