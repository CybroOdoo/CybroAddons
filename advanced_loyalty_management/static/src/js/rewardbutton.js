/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { RewardButton} from "@pos_loyalty/js/ControlButtons/RewardButton";
import { useListener } from "@web/core/utils/hooks";
const { Gui } = require('point_of_sale.Gui');
const { useState } = owl;
var rpc = require('web.rpc');

patch(RewardButton.prototype, "pos_loyalty_reward", {
    setup() {
        useListener('click', this.onClick);
        this.state = useState({
            frequency : 0,
        });
    },
    _mergeFreeProductRewards(freeProductRewards, potentialFreeProductRewards,redemption) {
        const result = []
        for (const reward of potentialFreeProductRewards) {
            if (!freeProductRewards.find(item => item.reward.id === reward.reward.id)) {
                result.push(reward);
            }
        }
        for (const rew of redemption){
            result.push(rew)
        }
        return freeProductRewards.concat(result);
    },
    _getPotentialRewards() {
        const order = this.env.pos.get_order();
        // Claimable rewards excluding those from eWallet programs.
        // eWallet rewards are handled in the eWalletButton.
        var pointCheck = false
        for (const pointChange of Object.values(order.couponPointChanges)){
            if(pointChange.coupon_id > 0){
                pointCheck = true
            }
        }
        let rewards = [];
        if (order) {
            const claimableRewards = order.getClaimableRewards();
            rewards = claimableRewards.filter(({ reward }) => reward.program_id.program_type !== 'ewallet');
        }
        const discountRewards = rewards.filter(({ reward }) => reward.reward_type == 'discount');
        const freeProductRewards = rewards.filter(({ reward }) => reward.reward_type == 'product');
        const redemption = rewards.filter(({ reward }) => reward.reward_type == 'redemption' && pointCheck == true
         && reward.redemption_frequency > this.state.frequency);
         if(order.partner != null){
            var checkFrequency =  this.check(rewards)
        }
        const potentialFreeProductRewards = order.getPotentialFreeProductRewards();
        return discountRewards.concat(this._mergeFreeProductRewards(freeProductRewards, potentialFreeProductRewards,redemption));
    },
    async check(rewards){
        //---to check how many times the reward is claimed
        let count = 0;
        const partner_id = this.env.pos.get_order().partner.id
        var checkRedemption = await rpc.query({
            model:'res.partner',
            method:'check_redemption',
            args:[partner_id]
        }).then((result)=>{
        const today = new Date()
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;
        const currentWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay());
        const currentWeekEnd = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (6 - today.getDay()));
        const formattedCurrentWeekStart = currentWeekStart.toISOString().split('T')[0];
        const formattedCurrentWeekEnd = currentWeekEnd.toISOString().split('T')[0];
        const currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        const currentMonthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of current month
        const formattedCurrentMonthStart = currentMonthStart.toISOString().split('T')[0];
        const formattedCurrentMonthEnd = currentMonthEnd.toISOString().split('T')[0];
        const currentYearStart = new Date(today.getFullYear(), 0, 1);
        const currentYearEnd = new Date(today.getFullYear(), 11, 31);
        const formattedCurrentYearStart = currentYearStart.toISOString().split('T')[0];
        const formattedCurrentYearEnd = currentYearEnd.toISOString().split('T')[0];
        for (const reward of rewards){
        if(reward.reward.redemption_frequency_unit === 'day'){
            for (let i = 0; i < result[1].length; i++) {
                if (result[1][i] === formattedDate) {
                    count ++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'week'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentWeekStart && date <= formattedCurrentWeekEnd) {
                    count++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'month'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentMonthStart && date <= formattedCurrentMonthEnd) {
                    count++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'year'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentYearStart && date <= formattedCurrentYearEnd) {
                    count ++

                }
            }
        }
        }
        return count
        })
        this.state.frequency = checkRedemption
    },

    async onClick() {
        //----change in work flow when reward type is redemption
        const rewards = this._getPotentialRewards();
        const order = this.env.pos.get_order();
        if (rewards.length === 0) {
            await this.showPopup('ErrorPopup', {
                title: this.env._t('No rewards available.'),
                body: this.env._t('There are no rewards claimable for this customer.')
            });
            return false;

        } else {
            const rewardsList = rewards.map((reward) => ({
                id: reward.reward.id,
                label: reward.reward.description,
                item: reward,
            }));
            const { confirmed, payload: selectedReward } = await this.showPopup('SelectionPopup', {
                title: this.env._t('Please select a reward'),
                list: rewardsList,
            });
            if (confirmed) {
            if(selectedReward.reward.reward_type == "redemption"){
            var points = []
            if(selectedReward.reward.max_redemption_type == 'points'){
                points.push(selectedReward.reward.max_redemption_amount/selectedReward.reward.redemption_amount)
            }
            else if(selectedReward.reward.max_redemption_type == 'amount'){
                points.push(selectedReward.reward.max_redemption_amount/selectedReward.reward.redemption_amount)
            }
            else if(selectedReward.reward.max_redemption_type == 'percent'){
                var totalAmount = order.get_total_with_tax()
                var maxRedemption = totalAmount * selectedReward.reward.max_redemption_amount / 100
                points.push(maxRedemption/selectedReward.reward.redemption_amount)
            }
                await Gui.showPopup("RewardPopup", {
                   title: this.env._t("Redeem Points"),
                   cancelText: this.env._t("Cancel"),
                   confirmText:this.env._t("Confirm"),
                   rewards: rewards,
                   selected_reward: selectedReward,
                   order: order,
                   max_redemption_points : points[0],
                   property: this
            });
            }else{
                return this._applyReward(selectedReward.reward, selectedReward.coupon_id, selectedReward.potentialQty);
            }
            }
        }
        return false;
    }
})
