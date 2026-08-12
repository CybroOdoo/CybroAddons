/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { HotelRoomPopup } from "@hotel_pos_extension/js/HotelRoomPopup";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";

export class HotelRoomSelectionButton extends Component {
    static template = "hotel_pos_extension.HotelRoomSelectionButton";
    static props = {};

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    get currentBookingName() {
        const order = this.pos.get_order();
        return order?.uiState?.roomName || _t("Add Room");
    }

    async click() {
        const bookings = await this.orm.searchRead(
            "room.booking",
            [["state", "=", "check_in"]],
            ["id", "name", "partner_id"]
        );

        if (bookings.length === 0) {
            this.notification.add(_t("No active hotel bookings found."), { type: "warning" });
            return;
        }

        const { confirmed, payload: selectedBooking } = await this.popup.add(HotelRoomPopup, {
            title: _t("Room Information"),
            bookings: bookings,
        });

        if (confirmed && selectedBooking) {
            const order = this.pos.get_order();
            order?.setBooking(selectedBooking);
            if (selectedBooking.partner_id) {
                const partner = this.pos.db.get_partner_by_id(selectedBooking.partner_id[0]);
                if (partner) {
                    order.set_partner(partner);
                }
            }
        }
    }
}

ProductScreen.addControlButton({
    component: HotelRoomSelectionButton,
    condition: function () {
        return true;
    },
});
