/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
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
        // Capture selectedOrder BEFORE calling super, as super.onDoRefund()
        // clears this.state.selectedOrder after processing the refund.
        const selectedOrder = this.state.selectedOrder;
        let pointsCost = [];
        if (selectedOrder) {
            let rewardLines = selectedOrder.get_orderlines().filter(
                (line) => line.is_reward_line == true
            );
            for (var line in rewardLines) {
                var dict = {};
                dict[rewardLines[line].coupon_id] = rewardLines[line].points_cost;
                pointsCost.push(dict);
            }
        }
        localStorage.setItem("pointsCost", JSON.stringify(pointsCost));
        // Await the async super call so state changes complete before returning.
        var res = await super.onDoRefund(...arguments);
        return res;
    },

    _onUpdateSelectedOrderline({ key, buffer }) {
        const order = this.getSelectedOrder();
        if (!order) {
            return this.numberBuffer.reset();
        }
        const selectedOrderlineId = this.getSelectedOrderlineId();
        const orderline = order.lines.find((line) => line.id == selectedOrderlineId);
        if (!orderline) {
            return this.numberBuffer.reset();
        }
        const toRefundDetails = orderline
            .getAllLinesInCombo()
            .map((line) => this.getToRefundDetail(line));
        for (const toRefundDetail of toRefundDetails) {
            // When already linked to an order, do not modify the to refund quantity.
            if (toRefundDetail.destionation_order_id) {
                return this.numberBuffer.reset();
            }
            const refundableQty = toRefundDetail.line.qty - toRefundDetail.line.refunded_qty;
            if (refundableQty <= 0) {
                return this.numberBuffer.reset();
            }
            if (buffer == null || buffer == "") {
                toRefundDetail.qty = 0;
            } else {
                const quantity = Math.abs(parseFloat(buffer));
                if(orderline.is_reward_line == true){
                    if(quantity > 0){
                        this.pos.notification.add(_t("REFUND NOT POSSIBLE FOR REWARD PRODUCT"), {
                                type: "error",
                                sticky: true,
                        });
                    }
                }
                else{
                    if (quantity > refundableQty) {
                        this.numberBuffer.reset();
                        return this.notification.add(_t(
                                "The requested quantity to be refunded is higher than the ordered quantity. %s is requested while only %s can be refunded.",
                                quantity,
                                refundableQty
                            ),{
                                type: "danger",
                            });
                    } else {
                        toRefundDetail.qty = quantity;
                    }
                }
            }
        }
    }
})