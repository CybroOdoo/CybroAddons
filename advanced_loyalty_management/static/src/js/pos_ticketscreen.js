/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(TicketScreen.prototype, {
    setup() {
        this.numberBuffer = useService("number_buffer");
        this.numberBuffer.use({
            triggerAtInput: (event) => this._onUpdateSelectedOrderline(event),
        });
        super.setup(...arguments);

    },
    async onDoRefund() {
    //---------to get the points cost from the reward lines
        var res = super.onDoRefund(...arguments);
        let rewardLines = this._state.ui.selectedOrder.get_orderlines().filter((line) => line.is_reward_line == true)
        let pointsCost = []
        for(var line in rewardLines ){
            var dict = {}
            dict[rewardLines[line].coupon_id] = rewardLines[line].points_cost
            pointsCost.push(dict)
        }
        localStorage.setItem("pointsCost", JSON.stringify(pointsCost))
        return res
    },

        _onUpdateSelectedOrderline({ key, buffer }) {
        //---prevent the rewarded to line to get refunded
        const order = this.getSelectedOrder();
        if (!order) {
            return this.numberBuffer.reset();
        }
        const selectedOrderlineId = this.getSelectedOrderlineId();
        const orderline = order.orderlines.find((line) => line.id == selectedOrderlineId);
        if (!orderline) {
            return this.numberBuffer.reset();
        }
        const toRefundDetails = orderline
            .getAllLinesInCombo()
            .map((line) => this._getToRefundDetail(line));
        for (const toRefundDetail of toRefundDetails) {
            if (toRefundDetail.destinationOrderUid) {
                return this.numberBuffer.reset();
            }
            const refundableQty =
                toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
            if (refundableQty <= 0) {
                return this.numberBuffer.reset();
            }
            if (buffer == null || buffer == "") {
                toRefundDetail.qty = 0;
            } else {
                const quantity = Math.abs(parseFloat(buffer));
                if(orderline.is_reward_line == true){
                if(quantity > 0){
                    this.popup.add(ErrorPopup, {
                        title: _t("REFUND NOT POSSIBLE"),
                        body: _t(
                            "You cannot refund a rewarded line",
                        ),
                    });
                }
                }
                else{
                if (quantity > refundableQty) {
                    this.numberBuffer.reset();
                    this.popup.add(ErrorPopup, {
                        title: _t("Maximum Exceeded"),
                        body: _t(
                            "The requested quantity to be refunded is higher than the ordered quantity. %s is requested while only %s can be refunded.",
                            quantity,
                            refundableQty
                        ),
                    });
                } else {
                    toRefundDetail.qty = quantity;
                }
                }
            }
        }
    }
})