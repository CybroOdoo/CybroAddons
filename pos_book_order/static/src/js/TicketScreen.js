/** @odoo-module **/
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    async onClickOrder(clickedOrder) {
    /**
    * Handles order selection on click.
    * If the order is a booked order, asks for confirmation
    * before navigating to the booked orders screen.
    */
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
                    self.pos.navigate('BookedOrdersScreen', {
                        data: result,
                        new_order: false
                    });
                })
            }
        } else {
            return super.onClickOrder(clickedOrder);
        }
    },
    async _setOrder(clickedOrder) {
    /**
    * Sets the selected order in POS.
    * Prompts confirmation for booked orders before
    * allowing navigation to the booked orders screen.
    */
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
                    self.pos.navigate('BookedOrdersScreen', {
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
