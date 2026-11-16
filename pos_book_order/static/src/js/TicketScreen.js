/** @odoo-module **/
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    async setOrder(order) {
        if (
            this.pos.config.enable &&
            order &&
            order.booking_ref_id &&
            !order.is_confirmed_booking &&
            !order.uiState?.is_confirmed_booking &&
            order.state === "draft" &&
            !order.finalized
        ) {
            const confirmed = await makeAwaitable(this.dialog, ConfirmationDialog, {
                title: _t("Confirm Booking"),
                body: _t(
                    "You have to confirm the booking to choose this order"
                ),
            });
            if (confirmed) {
                const result = await this.pos.data.call("book.order", "all_orders", []);
                this.pos.navigate("BookedOrdersScreen", {
                    data: result,
                    new_order: false,
                });
                return;
            }
        }
        return super.setOrder(order);
    },
});

