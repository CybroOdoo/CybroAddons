import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

export const SALON_PAGES = [
    "SalonScreen", "BookAppointmentScreen", "SlotBookingScreen",
    "ShowAppointmentsScreen", "WalkInAppointmentsScreen",
    "RunningAppointmentsScreen", "TrackAllAppointmentsScreen", "CommissionScreen",
];
const SYSTEM_PAGES = ["LoginScreen", "SaverScreen", "PaymentScreen", "ReceiptScreen"];

patch(PosStore.prototype, {
    get defaultPage() {
        if (this.config.is_salon) {
            return { page: "SalonScreen", params: {} };
        }
        return super.defaultPage;
    },

    navigate(routeName, routeParams = {}) {
        if (this.config.is_salon) {
            if (![...SALON_PAGES, ...SYSTEM_PAGES].includes(routeName)) {
                routeName = "SalonScreen";
                routeParams = {};
            }
        } else if (SALON_PAGES.includes(routeName)) {
            const d = super.defaultPage;
            routeName = d.page;
            routeParams = d.params;
        }
        return super.navigate(routeName, routeParams);
    },

    async handleUrlParams() {
        const cur = this.router.state.current;
        const bad = this.config.is_salon
            ? ![...SALON_PAGES, ...SYSTEM_PAGES].includes(cur)
            : SALON_PAGES.includes(cur);
        if (bad) {
            const d = this.defaultPage;
            this.navigate(d.page, d.params);
            return;
        }
        return super.handleUrlParams(...arguments);
    },
});