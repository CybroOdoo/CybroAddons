odoo.define('theme_boec.deal_week',function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    Animation.registry.best_deal = Animation.Class.extend({
        selector : '.deal_week_snippet_class',
        start: function () {
            var self = this;
            ajax.jsonRpc('/get_product', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
            ajax.jsonRpc('/get_countdown', 'call', {})
            .then(function(data){
                if(data){
                    var end_date = new Date(data).getTime();
                    var days, hours, minutes, seconds;
                    setInterval(function () {
                        var current_date = new Date().getTime();
                        var seconds_left = (end_date - current_date) / 1000;
                        days = parseInt(seconds_left / 86400);
                        seconds_left = seconds_left % 86400;
                        hours = parseInt(seconds_left / 3600);
                        seconds_left = seconds_left % 3600;
                        minutes = parseInt(seconds_left / 60);
                        seconds = parseInt(seconds_left % 60);
                        countdown.innerHTML = '<span class="days">' + days + ' <label>Days</label></span> <span class="hours">' + hours + ' <label>Hours</label></span> <span class="minutes">'
                        + minutes + ' <label>Minutes</label></span> <span class="seconds">' + seconds + ' <label>Seconds</label></span>';
                    }, 1000);
                }
            })
        },
    });
});
