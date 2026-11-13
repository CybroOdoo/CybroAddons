import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useSalonBookingActions } from "@pos_salon/app/hooks/salon_booking_actions";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { getLocalToday } from "@pos_salon/app/utils/salon_date";

export class RunningAppointmentsScreen extends Component {
    static template = "pos_salon.RunningAppointmentsScreen";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.actions = useSalonBookingActions({ onChange: () => this.loadRunningAppointments() });
        this.state = useState({
            appointments: [],
            loading: true,
            error: null,
        });

        this.loadRunningAppointments();
    }

    async loadRunningAppointments() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const today = getLocalToday();
            const result = await this.orm.searchRead(
                "salon.booking",
                [["state", "=", "confirmed"], ["date", "=", today]],
                ["customer_name", "customer_phone", "date", "slot", "time_period", "checked_in", "service_name", "state", "payment_state", "specialist_name", "amenity_names", "amount_payable", "amount_due"],
                { order: "date asc, id asc" }
            );

            const now = new Date();

            this.state.appointments = result.filter((appt) => {
                const [from, to] = (appt.time_period || "").split(" - ");
                if (!from || !to) return false;
                const startTime = this._getDateTime(appt.date, from);
                const endTime = this._getDateTime(appt.date, to);
                return now >= startTime && now <= endTime;
            });

        } catch (error) {
            this.state.error = error.data?.message || error.message || _t("Network error");
        } finally {
            this.state.loading = false;
        }
    }

    _getDateTime(dateStr, timeStr) {
        const [time, modifier] = timeStr.trim().split(" ");
        let [hours, minutes] = time.split(":").map(Number);
        if (modifier === "PM" && hours < 12) hours += 12;
        if (modifier === "AM" && hours === 12) hours = 0;
        const d = new Date(dateStr + "T00:00");
        d.setHours(hours, minutes, 0, 0);
        return d;
    }

    lateMinutes(appt) {
        if (appt.checked_in) return 0;
        const from = (appt.time_period || "").split(" - ")[0];
        if (!from) return 0;
        const diff = new Date() - this._getDateTime(appt.date, from);
        return Math.max(0, Math.floor(diff / 60000));
    }

    refresh() {
        this.loadRunningAppointments();
    }

    back() {
        this.pos.router.navigate("SalonScreen");
    }
}

registry.category("pos_pages").add("RunningAppointmentsScreen", {
    name: "RunningAppointmentsScreen",
    component: RunningAppointmentsScreen,
    route: `/pos/ui/${odoo.pos_config_id}/running-appointments`,
});
