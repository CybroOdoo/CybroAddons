odoo.define('advanced_loyalty_management.Order', function(require) {
    "use strict";

    const models = require('point_of_sale.models');
    const _super_Order = models.Order.prototype;
    const { patch } = require('web.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');


    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            if (options?.json?.lines.length === 0) {
                this.additional_redeemed_points = 0;
                this.pointsWon = 0;
                this.selected_reward = null;
            }
        },

        get_won_points: function() {
            const wonPoints = _super_Order.get_won_points.apply(this, arguments);
            if (this.selected_reward && this.selected_reward.reward_type === 'redemption') {
                return Math.max(0, this.pointsWon - this.additional_redeemed_points);
            }
            return wonPoints;
        },

        get_spent_points: function() {
            const spentPoints = _super_Order.get_spent_points.apply(this, arguments);
            return spentPoints + this.additional_redeemed_points;
        },

        get_new_points: function() {
            const newPoints = _super_Order.get_new_points.apply(this, arguments);
            if (this.selected_reward && this.selected_reward.reward_type === 'redemption') {
                return Math.max(0, this.pointsWon - this.additional_redeemed_points);
            }
            return newPoints;
        },
                  // Ensure pointsWon, additional_redeemed_points, selected_reward is also persisted
        export_as_JSON: function() {
            const json = _super_Order.export_as_JSON.apply(this, arguments);
            json.additional_redeemed_points = this.additional_redeemed_points;
            json.selected_reward = this.selected_reward;
            json.pointsWon = this.pointsWon;
            return json;
        },
                    // Restore pointsWon, additional_redeemed_points, selected_reward
        init_from_JSON: function(json) {
            _super_Order.init_from_JSON.apply(this, arguments);
            this.additional_redeemed_points = json.additional_redeemed_points || 0;
            this.selected_reward = json.selected_reward || null;
            this.pointsWon = json.pointsWon || 0;
        },

        applyRedeemPoints: function(pointsToRedeem, selectedReward, pointsWon) {
            this.additional_redeemed_points += pointsToRedeem;
            this.selected_reward = selectedReward;
            this.pointsWon = pointsWon;
        },
        resetRedemptionPoints: function() {
            this.additional_redeemed_points = 0;
            this.pointsWon = 0;
            this.selected_reward = null;
        }
    });
                // Resets the loyalty points on clicking backspace
    patch(ProductScreen.prototype, 'advanced_loyalty_management.ProductScreen', {
            _updateSelectedOrderline: function (event) {
                let screen = this._super(...arguments);
                const order = this.env.pos.get_order()
                const selectedLine = order?.selected_orderline?.get_reward()?.reward_type;
                if (selectedLine === 'redemption') {
                    order.resetRedemptionPoints();
                    this.render();
                }
                return screen;
            },
        });

    return models;
});
