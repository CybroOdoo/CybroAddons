odoo.define('advanced_loyalty_management.RewardPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    const { hooks } = owl;
    const { useState, useRef } = hooks;

    class RewardPopup extends AbstractAwaitablePopup {
        setup() {
            this.state = useState({
                value: '',
                redeemPoints: ''
            });
            this.points = useRef("points");
        }

        toRedeem(ev) {
            this.state.redeemPoints = this.points.el.value;
        }

        save(props, ev) {
            const pointsToRedeem = parseInt(this.state.redeemPoints);
            if (isNaN(pointsToRedeem)) {
                this.showPopup('ErrorPopup', {
                    title: _t('Error'),
                    body: _t('Please enter a valid number'),
                });
                return;
            }

            if (props.max_redemption_points < pointsToRedeem) {
                this.showPopup('ErrorPopup', {
                    title: _t('Error'),
                    body: _t('Points to redeem should be less than Maximum Redemption Point.'),
                });
                return;
            }

            const selectedReward = props.selected_reward;
            selectedReward.pointsToRedeem = parseInt(this.state.redeemPoints);
            const pointsWon = props.order.get_won_points();
            props.order.point_cost = pointsToRedeem;
            ev.confirm();
            props.property.apply_reward(selectedReward);
            props.order.applyRedeemPoints(pointsToRedeem, selectedReward, pointsWon);
        }
    }

    RewardPopup.template = 'RewardPopup';
    RewardPopup.defaultProps = {
        confirmText: _t('Confirm'),
        cancelText: _t('Cancel'),
        title: _t('Reward'),
        body: '',
    };

    Registries.Component.add(RewardPopup);

    return RewardPopup;
});
