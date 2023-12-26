/** @odoo-module */

import animations from "@website/js/content/snippets.animation";
import {
    jsonrpc
} from "@web/core/network/rpc_service";

animations.registry.best_deal = animations.Class.extend({
    selector: '.deal_week_snippet_class',
    start: function() {
        var self = this;
        jsonrpc('/get_product')
            .then(function(data) {
                if (data) {
                    self.$target.empty().append(data);
                }
            });
        jsonrpc('/get_countdown')
            .then(function(data) {
                if (data) {
                    var end_date = new Date(data).getTime();
                    var days, hours, minutes, seconds;
                    var countdown_div = $("#countdown")[0];
                    setInterval(function() {
                        var current_date = new Date().getTime();
                        var seconds_left = (end_date - current_date) / 1000;
                        var countdown_div = $("#countdown")[0];
                        days = parseInt(seconds_left / 86400);
                        seconds_left = seconds_left % 86400;
                        hours = parseInt(seconds_left / 3600);
                        seconds_left = seconds_left % 3600;
                        minutes = parseInt(seconds_left / 60);
                        seconds = parseInt(seconds_left % 60);
                        if (countdown_div) {
                            countdown_div.innerHTML = '<span class="days">' + days + ' <label>Days</label></span> <span class="hours">' + hours + ' <label>Hours</label></span> <span class="minutes">' +
                                minutes + ' <label>Minutes</label></span> <span class="seconds">' + seconds + ' <label>Seconds</label></span>';
                        }
                    }, 1000);
                }
            })
    },
});
