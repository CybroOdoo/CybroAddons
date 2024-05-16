/** @odoo-module **/

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
 async onClickOrder(clickedOrder) {
            if (clickedOrder.booking_ref_id){
            const { confirmed } = await this.popup.add(ConfirmPopup, {
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
            new_order:false
            });
            })
            }
            }
            else{
            return super.onClickOrder(clickedOrder);
            }
        },
 async _setOrder(clickedOrder) {
            if (clickedOrder.booking_ref_id){
            const { confirmed } = await this.popup.add(ConfirmPopup, {
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
            new_order:false
            });
            })
            }
            }
            else{
            return super._setOrder(clickedOrder);
            }
        }
});
