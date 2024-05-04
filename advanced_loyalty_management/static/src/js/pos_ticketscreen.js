odoo.define('advanced_loyalty_management.TicketScreen', function (require) {
    'use strict';
    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { parse } = require('web.field_utils');
    const {_t} = require('web.core');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const LoyaltyRefundTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
        async _onDoRefund() {
            //----points cost is stored to local storage when the parent order has reward lines
            var res = super._onDoRefund()
            let pointsCost = []
            var refundOrder = this._state.syncedOrders.cache[this._state.ui.selectedSyncedOrderId]
            var rewardLines = refundOrder._get_reward_lines()
            for(var line in rewardLines ){
                var dict = {}
                dict[rewardLines[line].coupon_id] = rewardLines[line].points_cost
                pointsCost.push(dict)
            }
            localStorage.setItem("pointsCost", JSON.stringify(pointsCost))
            return res
        }

        _onUpdateSelectedOrderline({ detail }) {
            //----to prevent the return of reward lines
            const buffer = detail.buffer;
            const order = this.getSelectedSyncedOrder();
            if (!order) return NumberBuffer.reset();
            let pointsCost = []
            var reward_product_id = []
            var refundOrder = this._state.syncedOrders.cache[this._state.ui.selectedSyncedOrderId]
            var rewardLines = refundOrder._get_reward_lines()
            for(var line in rewardLines ){
                var dict = {}
                dict[rewardLines[line].coupon_id] = rewardLines[line].points_cost
                pointsCost.push(dict)
                reward_product_id.push(rewardLines[line].product.id)
            }
            const selectedOrderlineId = this.getSelectedOrderlineId();
            const orderline = order.orderlines.find((line) => line.id == selectedOrderlineId);
            if (!orderline) return NumberBuffer.reset();
            const toRefundDetail = this._getToRefundDetail(orderline);
            // When already linked to an order, do not modify the to refund quantity.
            if (toRefundDetail.destinationOrderUid) return NumberBuffer.reset();
            const refundableQty = toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
            if (refundableQty <= 0) return NumberBuffer.reset();
            if (buffer == null || buffer == '') {
                toRefundDetail.qty = 0;
            } else {
                const quantity = Math.abs(parse.float(buffer));
                if(orderline.is_reward_line == true || orderline.product.id == reward_product_id[0] -1){
                if(quantity > 0){
                    this.showPopup('ErrorPopup', {
                        title: _t("REFUND NOT POSSIBLE"),
                        body: _t(
                            "You cannot refund a rewarded line",
                        ),
                    });
                }
                }
                else{
                if (quantity > refundableQty) {
                    NumberBuffer.reset();
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Maximum Exceeded'),
                        body: _.str.sprintf(
                            this.env._t(
                                'The requested quantity to be refunded is higher than the ordered quantity. %s is requested while only %s can be refunded.'
                            ),
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
    Registries.Component.extend(TicketScreen, LoyaltyRefundTicketScreen);
});
