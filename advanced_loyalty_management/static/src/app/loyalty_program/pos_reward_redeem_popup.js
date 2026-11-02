/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { Component, signal, proxy, props, types} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { Dialog } from "@web/core/dialog/dialog";

export class RewardPopup extends Component {
    static template = "advanced_loyalty_management.RedeemPoint";
    static components = { Dialog };
    props = props({
        title: String,
        rewards: types.array,
        selected_reward: types.object,
        order: types.object,
        max_redemption_points: types.number,
        property: types.object,
        coupon_id: { type: types.any, optional: true },
        close: types.function,
    });
    points = signal.ref();
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({
            value: '',
            redeemPoints: ''
        })
    }

    toRedeem(ev) {
        ev.state.redeemPoints = ev.points()?.value || "";
    }

    validateRedeemPoints() {
        const value = this.state.redeemPoints;

        if (value === "" || value === null || value === undefined) {
            this.dialog.add(WarningDialog, {
                message: _t("Please enter points to redeem."),
            });
            return false;
        }

        const points = Number(value);

        if (!Number.isFinite(points)) {
            this.dialog.add(WarningDialog, {
                message: _t("Points to redeem should be a number."),
            });
            return false;
        }

        if (!Number.isInteger(points)) {
            this.dialog.add(WarningDialog, {
                message: _t("Points to redeem should be a whole number."),
            });
            return false;
        }

        if (points <= 0) {
            this.dialog.add(WarningDialog, {
                message: _t("Points to redeem should be greater than 0."),
            });
            return false;
        }

        if (points > this.props.max_redemption_points) {
            this.dialog.add(WarningDialog, {
                message: _t(
                    "Points to redeem should be less than or equal to the Maximum Redemption Points."
                ),
            });
            return false;
        }

        const order = this.props.order;
        const program = this.props.selected_reward?.reward?.program_id;
        const card = this.props.property?.pos?.models?.["loyalty.card"]?.find(
            (c) =>
                c.program_id?.id === program?.id &&
                c.partner_id?.id === order?.partner_id?.id
        );
        if (card && points > card.points) {
            this.dialog.add(WarningDialog, {
                message: _t(
                    "Points to redeem cannot exceed the customer's available card balance."
                ),
            });
            return false;
        }

        return true;
    }

    save(props, ev) {
        // Stop here if the entered value is invalid.
        if (!this.validateRedeemPoints()) {
            return false;
        }

        const redeemPoints = Number(ev.state.redeemPoints);
        const selectedReward = props.selected_reward;

        selectedReward.reward.pointsToRedeem = redeemPoints;

        props.order.selectedCoupon = selectedReward.coupon_id;
        props.order.pointsCost = redeemPoints;

        const result = props.property._applyReward(
            selectedReward.reward,
            selectedReward.coupon_id,
            selectedReward.potentialQty
        );

        if (result) {
            props.close();
        }

        return result;
    }

    cancel() {
        this.props.close();
    }

}