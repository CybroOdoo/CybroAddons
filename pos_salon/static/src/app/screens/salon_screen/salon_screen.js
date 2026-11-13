import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { registry } from "@web/core/registry";

export class SalonScreen extends Component {
    static template = "pos_salon.SalonScreen";

    setup() {
        this.pos = usePos();
        this.state = useState({ message: "Welcome to Salon POS" });

    }

    openBookAppointment() {
        if (this.pos.router) {
            this.pos.router.navigate("BookAppointmentScreen");
        }
    }

    openTrackAllAppointments() {
        if (this.pos.router) {
            this.pos.router.navigate("TrackAllAppointmentsScreen");
        }
    }

    openWalkInAppointments() {
        if (this.pos.router) {
            this.pos.router.navigate("WalkInAppointmentsScreen");
        }
    }

    openCommission() {
        if (this.pos.router) {
            this.pos.router.navigate("CommissionScreen");
        }
    }
}

registry.category("pos_pages").add("SalonScreen", {
    name: "SalonScreen",
    component: SalonScreen,
    route: `/pos/ui/${odoo.pos_config_id}/salon`,
});