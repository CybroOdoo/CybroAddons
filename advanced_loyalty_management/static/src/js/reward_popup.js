/** @odoo-module **/

import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
const { useState,useRef } = owl;
import { _t } from 'web.core';


class RewardPopup extends AbstractAwaitablePopup {
    setup(){
        this.state = useState({
            value:'' ,
            redeemPoints:''
        })
        this.points = useRef("points");
    }

    toRedeem(ev){
        ev.state.redeemPoints = ev.points.el.value
    }

    save(props,ev){
    //---after giving the points to redeem, the reward is added to orderline
        if(isNaN(ev.state.redeemPoints)){
            ev.showPopup('ErrorPopup', {
                title: ev.env._t('Error'),
                body: ev.env._t('Please enter a valid number'),
            });
        }else if(ev.props.max_redemption_points < ev.state.redeemPoints){
           ev.showPopup('ErrorPopup', {
                title: ev.env._t('Error'),
                body: ev.env._t('Points to redeem should be less than Maximum Redemption Point.'),
            });
        }
        else{
        const selectedReward = props.selected_reward
        const pointsWon = props.order.couponPointChanges[selectedReward.coupon_id].points
        const order = props.order.access_token
        selectedReward.reward.pointsToRedeem = parseInt(ev.state.redeemPoints)
        ev.confirm()
        props.order.selectedCoupon = selectedReward.coupon_id
        props.order.pointsCost = parseInt(ev.state.redeemPoints)
        return props.property._applyReward(
            selectedReward.reward,
            selectedReward.coupon_id,
            selectedReward.potentialQty
        );
    }
    }
    }
RewardPopup.template = 'RewardPopup';
    RewardPopup.defaultProps = {
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        title: 'Loyalty Programs',
        body: '',
    };
Registries.Component.add(RewardPopup);
return RewardPopup;
