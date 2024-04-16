    /** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useRef,useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

export class RewardPopup extends AbstractAwaitablePopup {
    static template = "RedeemPoint";
    setup(){
        this.orm = useService("orm");
        this.popup = useService("popup");
        this.state = useState({
            value:'' ,
            redeemPoints:''
        })
        this.points = useRef("points");
    }

    toRedeem(ev){
    //---validation for popup---
            ev.state.redeemPoints = ev.points.el.value
        if (isNaN(ev.state.redeemPoints)) {
            ev.popup.add(ErrorPopup, {
                body: _t(
                    "Points to redeem should be a number."
                ),
            });
        } else if (ev.props.max_redemption_points < ev.state.redeemPoints) {
            ev.popup.add(ErrorPopup, {
                body: _t(
                "Points to redeem should be less than Maximum Redemption Point."
                ),
            });
        }
    }

    save(props,ev){
    //---after giving the points to redeem, the reward is added to orderliness
        const selectedReward = props.selected_reward
        const pointsOfPartner = props.order.partner.loyalty_cards[selectedReward.coupon_id].points
        const pointsWon = props.order.couponPointChanges[selectedReward.coupon_id].points
        const balance = pointsOfPartner + pointsWon - parseInt(ev.state.redeemPoints)
        const order = props.order.access_token
        selectedReward.reward.pointsToRedeem = parseInt(ev.state.redeemPoints)
        props.close()
        props.order.selectedCoupon = selectedReward.coupon_id
        props.order.pointsCost = parseInt(ev.state.redeemPoints)
        return props.property._applyReward(
            selectedReward.reward,
            selectedReward.coupon_id,
            selectedReward.potentialQty
        );

    }
    static defaultProps = {
        closePopup: _t("Cancel"),
        confirmText: _t("Save"),
        title: _t("Customer Details"),
    };
}