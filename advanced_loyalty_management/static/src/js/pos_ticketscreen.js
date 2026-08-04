/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(TicketScreen.prototype, {
    setup() {
        this.numberBuffer = useService("number_buffer");
        this.notification = useService("notification");
        this.numberBuffer.use({
            triggerAtInput: (event) => this._onUpdateSelectedOrderline(event),
        });
        super.setup(...arguments);
    },

    _getSearchFields() {
        const fields = super._getSearchFields(...arguments);
        for (const key in fields) {
            const originalRepr = fields[key].repr;
            fields[key].repr = (order) => {
                const res = originalRepr(order);
                if (res === false || res === undefined || res === null) {
                    return "";
                }
                return String(res);
            };
        }
        return fields;
    },

    async onDoRefund() {
        //To get the points cost from the reward lines
        const order = this.getSelectedOrder();
        if (order) {
            const rewardLines = order.getOrderlines().filter((line) => line.is_reward_line);
            const pointsCost = [];
            for (const line of rewardLines) {
                if (line.coupon_id) {
                    const dict = {};
                    dict[line.coupon_id.id || line.coupon_id] = line.points_cost;
                    pointsCost.push(dict);
                }
            }
            localStorage.setItem("pointsCost", JSON.stringify(pointsCost));
        }
        return super.onDoRefund(...arguments);
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
            if (toRefundDetail.destination_order_uuid) {
                return this.numberBuffer.reset();
            }
            const refundableQty = toRefundDetail.line.qty - toRefundDetail.line.refundedQty;
            if (refundableQty <= 0) {
                return this.numberBuffer.reset();
            }
            if (buffer == null || buffer == "") {
                toRefundDetail.qty = 0;
            } else {
                const quantity = Math.abs(parseFloat(buffer));
                if (orderline.is_reward_line == true) {
                    if (quantity > 0) {
                        this.numberBuffer.reset();
                        this.notification.add(_t("REFUND NOT POSSIBLE FOR REWARD PRODUCT"), {
                            type: "danger",
                            sticky: true,
                        });
                        return;
                    }
                }
                else {
                    if (quantity > refundableQty) {
                        this.numberBuffer.reset();
                        return this.notification.add(_t(
                            "The requested quantity to be refunded is higher than the ordered quantity. %s is requested while only %s can be refunded.",
                            quantity,
                            refundableQty
                        ), {
                            type: "danger",
                        });
                    } else {
                        toRefundDetail.qty = quantity;
                    }
                }
            }
        }
    },

    _isEWalletGiftCard(orderline) {
        if (!orderline) {
            return false;
        }
        return super._isEWalletGiftCard(...arguments);
    }
});