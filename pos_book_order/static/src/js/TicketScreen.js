/** @odoo-module **/
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    /**
     * Handles click event on a POS order.
     * If the order is a booked order, the user must
     * confirm the booking before accessing it.
     * Otherwise, the default TicketScreen behavior runs.
     */
    async onClickOrder(clickedOrder) {
        if (clickedOrder.booking_ref_id) {
            const {
                confirmed
            } = await this.popup.add(ConfirmationDialog, {
                title: _t("Confirm Booking"),
                body: _t(
                    "You have to confirm the booking to choose this order"
                ),
            });
            if (confirmed) {
                var self = this
                await this.orm.call(
                    "book.order", "all_orders", [], {}
                ).then(function(result) {
                    self.pos.showScreen('BookedOrdersScreen', {
                        data: result,
                        new_order: false
                    });
                })
            }
        } else {
            return super.onClickOrder(clickedOrder);
        }
    },
    /**
     * Overrides order selection behavior.
     * If the order is linked to a booking,
     * the user must confirm the booking first.
     */
    async _setOrder(clickedOrder) {
        if (clickedOrder.booking_ref_id) {
            const {
                confirmed
            } = await this.popup.add(ConfirmPopup, {
                title: _t("Confirm Booking"),
                body: _t(
                    "You have to confirm the booking to choose this order"
                ),
            });
            if (confirmed) {
                var self = this
                await this.orm.call(
                    "book.order", "all_orders", [], {}
                ).then(function(result) {
                    self.pos.showScreen('BookedOrdersScreen', {
                        data: result,
                        new_order: false
                    });
                })
            }
        } else {
            return super._setOrder(clickedOrder);
        }
    }
});
