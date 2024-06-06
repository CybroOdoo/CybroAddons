/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";

publicWidget.registry.BestDeal = animations.Animation.extend({
 // To extend public widget
        selector: '.best_deal',
         events: {
            'click .btn-buy-now': '_onClickBuyNow',
        },
         init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
        },
        _onClickBuyNow: function (ev) {
            var $target = $(ev.currentTarget);
            var productId = $target.data('product-id');
            var self = this;
            jsonrpc('/shop/cart/update_json', {
            display: false,
                'product_id': productId,
                'add_qty': 1,
            }).then(async function (result) {
                wSaleUtils.updateCartNavBar(result);
                wSaleUtils.showWarning(result.notification_info.warning);
                wSaleUtils.showCartNotification(self.call.bind(self), result.notification_info);
                // Propagating the change to the express checkout forms
                Component.env.bus.trigger('cart_amount_changed', [result.amount, result.minor_amount])
            });
        },
         start: async function () {
          // To get data from controller.
        var self = this;
        await jsonrpc('/get_product', {}).then(function(data) {
            if (data) {
                       self.$target.html(data)
                    }
        });
        await jsonrpc('/get_countdown', {}).then(function(data) {
    if (data) {
        var end_date = new Date(data).getTime();
        var days, hours, minutes, seconds;
        setInterval(function() {
            var start_date = new Date().getTime();
            var seconds_left = (end_date - start_date) / 1000;
            days = Math.abs(parseInt(seconds_left / 86400));
            seconds_left = seconds_left % 86400;
            hours = Math.abs(parseInt(seconds_left / 3600));
            seconds_left = seconds_left % 3600;
            minutes = Math.abs(parseInt(seconds_left / 60));
            seconds = Math.abs(parseInt(seconds_left % 60));
            $("#countdown").html('<span class="days">' + days +
            ' <label>Days</label></span> <span class="hours">' + hours +
            ' <label>Hours</label></span> <span class="minutes">' +minutes +
            ' <label>Minutes</label></span> <span class="seconds">' + seconds +
            ' <label>Seconds</label></span>');
        }, 1000);
    }
    });
    }
})
