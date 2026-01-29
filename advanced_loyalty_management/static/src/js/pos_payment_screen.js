odoo.define('advanced_loyalty_management.ChangeLoyalty', function (require) {
    "use strict";
    const { patch } = require('web.utils');
    const PaymentScreenStatus = require('point_of_sale.PaymentScreenStatus');
    const { Gui } = require('point_of_sale.Gui');

    patch(PaymentScreenStatus.prototype, 'point_of_sale/static/src/js/Screens/PaymentScreen/PaymentScreenStatus.js', {
        async convertLoyalty() {
            var order = this.env.pos.get_order();
            const result = await Gui.showPopup('LoyaltyPrograms', {
                title: this.env._t('Convert Change'),
                cancelText: this.env._t("Cancel"),
                confirmText: this.env._t("Confirm"),
                Order: order,
                Loyalty: this.env.pos.loyalty,
                LoyaltyPoints: order.get_won_points(),
                change: order.get_change(),
            });
        },

        showLoyaltyButton: function() {
            var order = this.env.pos.get_order();
            const showButton = order.get_change() > 0 && order.get_won_points() > 0
            return showButton;
        },
    });
    // Patch the Order prototype to modify get_won_points and adds the change
    const Order = require('point_of_sale.models').Order;
    patch(Order.prototype, 'advanced_loyalty_management.Order', {
        get_won_points: function () {
            let points = this._super(...arguments);
            if (this.change_to_loyalty) {
                points += this.change_to_loyalty;
            }
            return points;
        },
    });
});
