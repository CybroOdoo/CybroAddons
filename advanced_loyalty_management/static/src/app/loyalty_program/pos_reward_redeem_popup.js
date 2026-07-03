/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { useRef,useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class RewardPopup extends Component {
    static template = "RedeemPoint";
    static components = { Dialog };
     static defaultProps = {
        closePopup: _t("Cancel"),
        confirmText: _t("Save"),
        title: _t("Customer Details"),
    };
    setup(){
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            value:'' ,
            redeemPoints:''
        })
        this.points = useRef("points");
    }

    toRedeem(ev){
    //---Validation for popup---
        ev.state.redeemPoints = ev.points.el.value
        if (isNaN(ev.state.redeemPoints)) {
            ev.dialog.add(WarningDialog, {
                message: _t(
                    "Points to redeem should be a number."
                ),
            });
        } else if (ev.props.max_redemption_points < ev.state.redeemPoints) {
            ev.dialog.add(WarningDialog, {
                message: _t(
                "Points to redeem should be less than Maximum Redemption Point."
                ),
            });
        }
    }
   save(props,ev){
        const selectedReward = props.selected_reward
        const loyaltyPoints = props.order.getLoyaltyPoints()
        const pointsWon = loyaltyPoints[0].points.won
        const balance = loyaltyPoints[0].points.total - parseInt(ev.state.redeemPoints)
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

}