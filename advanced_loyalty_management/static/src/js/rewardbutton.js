odoo.define('advanced_loyalty_management.RewardButton', function (require) {
    "use strict";
const { patch } = require('web.utils');
const { useListener } = require('web.custom_hooks');
const RewardButton = require('pos_loyalty.RewardButton');
const { Gui } = require('point_of_sale.Gui');
const { _t } = require('web.core');
const { useState } = owl;
var models = require('point_of_sale.models');
var rpc = require('web.rpc');
var utils = require('web.utils');
var round_pr = utils.round_precision;
models.load_fields("loyalty.reward",
 ["max_redemption_amount", "redemption_point", "redemption_amount","redemption_frequency","redemption_frequency_unit",
  "redemption_eligibility", "max_redemption_type"]);
models.load_fields("loyalty.program",
 ["point_rate"]);

patch(RewardButton.prototype, "pos_loyalty/static/src/js/RewardButton.js", {
    setup() {
        useListener('click', this.onClick);
        this.state = useState({
            frequency : 0,
        });
    },
    async apply_reward(reward) {
        const order = this.env.pos.get_order();
        var client = order.get_client();
        var product, product_price, order_total, spendable;
        var crounding;

        if (!client) {
            return;
        } else if (reward.reward_type === 'gift') {
            product = order.pos.db.get_product_by_id(reward.gift_product_id[0]);

            if (!product) {
                return;
            }

            let options = await order._getAddProductOptions(product);
            await order.add_product(product, {
                ...options,
                price: 0,
                quantity: 1,
                merge: false,
                extras: { reward_id: reward.id, price_manually_set: true, is_reward_line: true },
            });

        } else if (reward.reward_type === 'discount') {

            crounding = order.pos.currency.rounding;
            spendable = order.get_spendable_points();
            order_total = order.get_total_with_tax();
            var discount = 0;

            product = order.pos.db.get_product_by_id(reward.discount_product_id[0]);

            if (!product) {
                return;
            }

            if (reward.discount_type === "percentage") {
                if (reward.discount_apply_on === "on_order") {
                    discount += round_pr(order_total * (reward.discount_percentage / 100), crounding);
                }

                if (reward.discount_apply_on === "specific_products") {
                    for (var prod of reward.discount_specific_product_ids) {
                        var specific_products = order.pos.db.get_product_by_id(prod);

                        if (!specific_products)
                            return;

                        for (var line of order.get_orderlines()) {
                            if (line.product.id === specific_products.id)
                                discount += round_pr(line.get_price_with_tax() * (reward.discount_percentage / 100), crounding);
                        }
                    }
                }

                if (reward.discount_apply_on === "cheapest_product") {
                    var price;
                    for (var line of order.get_orderlines()) {
                        if ((!price || price > line.get_unit_price()) && line.product.id !== product.id) {
                            discount = round_pr(line.get_price_with_tax() * (reward.discount_percentage / 100), crounding);
                            price = line.get_unit_price();
                        }
                    }
                }
                if (reward.discount_max_amount !== 0 && discount > reward.discount_max_amount)
                    discount = reward.discount_max_amount;

                let options = await order._getAddProductOptions(product);
                await order.add_product(product, {
                    ...options,
                    price: -discount,
                    quantity: 1,
                    merge: false,
                    extras: { reward_id: reward.id, price_manually_set: true, is_reward_line: true },
                });
            }
            if (reward.discount_type == "fixed_amount") {
                let discount_fixed_amount = reward.discount_fixed_amount;
                let point_cost = reward.point_cost;
                let quantity_to_apply = Math.floor(spendable / point_cost);
                let amount_discounted = discount_fixed_amount * quantity_to_apply;

                if (amount_discounted > order_total) {
                    quantity_to_apply = Math.floor(order_total / discount_fixed_amount);
                }

                let options = await order._getAddProductOptions(product);
                await order.add_product(product, {
                    ...options,
                    price: -discount_fixed_amount,
                    quantity: quantity_to_apply,
                    merge: false,
                    extras: { reward_id: reward.id, price_manually_set: true, is_reward_line: true },
                });
            }
        }
        // Start of new condition for reward_type 'redemption'
        else if (reward.reward_type === 'redemption') {
            if (order.get_client() != null) {
                await this.check(reward, order.get_client().id);
            }

            if (reward.redemption_frequency > this.state.frequency) {
                product = this.env.pos.db.get_product_by_id(reward.discount_product_id[0]);
                if (!product) {
                    return;
                }

                let options = await order._getAddProductOptions(product);
                await order.add_product(product, {
                    ...options,
                    price: -reward.pointsToRedeem,
                    quantity: 1,
                    merge: false,
                    extras: { reward_id: reward.id, price_manually_set: true, is_reward_line: true },
                });
            } else {
                this.showPopup('ErrorPopup', {
                    title: _t("REDEMPTION LIMIT REACHED"),
                    body: _t("You have reached the redemption limit for this period."),
                });
            }
        }
    },

    async check(reward, partnerId){
        //---To check how many times the reward is claimed
        let count = 0;
        var checkRedemption = await rpc.query({
            model:'res.partner',
            method:'check_redemption',
            args:[partnerId]
        })
        .then((result)=>{
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
        if(reward.redemption_frequency_unit === 'day'){
            for (let i = 0; i < result[1].length; i++) {
                if (result[1][i] === formattedDate) {
                    count ++;
                }
            }
        }
        else if(reward.redemption_frequency_unit === 'week'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentWeekStart && date <= formattedCurrentWeekEnd) {
                    count++;
                }
            }
        }
        else if(reward.redemption_frequency_unit === 'month'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentMonthStart && date <= formattedCurrentMonthEnd) {
                    count++;
                }
            }
        }
        else if(reward.redemption_frequency_unit === 'year'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentYearStart && date <= formattedCurrentYearEnd) {
                    count ++

                }
            }
        }
        return count
        })
        this.state.frequency = checkRedemption
    },
    async onClick() {
        const order = this.env.pos.get_order();
        const rewards = order.get_available_rewards();
        const client = order.get_client();

        if (rewards.length === 0) {
            await this.showPopup('ErrorPopup', {
                title: this.env._t('No rewards available.'),
                body: this.env._t('There are no rewards claimable for this customer.')
            });
            return false;
        }

        let rewardPoints = 0;
        if (client) {
            rewardPoints = client.loyalty_points || 0;
        }

        const filteredRewards = rewards.filter(reward => {
            if (reward.reward_type === 'redemption') {
                return rewardPoints > 0;
            }
            return true;
        });

        if (filteredRewards.length === 0) {
            await this.showPopup('ErrorPopup', {
                title: this.env._t('No claimable rewards.'),
                body: this.env._t('There are no rewards claimable for this customer.')
            });
            return false;
        }

        const rewardsList = filteredRewards.map((reward) => ({
            id: reward.id,
            label: reward.name,
            item: reward,
        }));

        const { confirmed, payload: selectedReward } = await this.showPopup('SelectionPopup', {
            title: this.env._t('Please select a reward'),
            list: rewardsList,
        });

        if (confirmed) {
            if (selectedReward.reward_type == "redemption") {
                var points = [];
                if (selectedReward.max_redemption_type == 'points') {
                    points.push(selectedReward.max_redemption_amount / selectedReward.redemption_amount);
                } else if (selectedReward.max_redemption_type == 'amount') {
                    points.push(selectedReward.max_redemption_amount / selectedReward.redemption_amount);
                } else if (selectedReward.max_redemption_type == 'percent') {
                    var totalAmount = order.get_total_with_tax();
                    var maxRedemption = totalAmount * selectedReward.max_redemption_amount / 100;
                    points.push(maxRedemption / selectedReward.redemption_amount);
                }
                Gui.showPopup('RewardPopup', {
                    title: this.env._t('Reward'),
                    cancelText: this.env._t("Cancel"),
                    confirmText: this.env._t("Confirm"),
                    rewards: rewards,
                    selected_reward: selectedReward,
                    order: order,
                    max_redemption_points: points[0],
                    property: this
                });
            } else {
                return this.apply_reward(selectedReward);
            }
        }
        return false;
    }
  })
})
