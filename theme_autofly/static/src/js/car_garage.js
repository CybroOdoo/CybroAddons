odoo.define('theme_autofly.car_garage', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const { qweb } = require('web.core');
    var ajax = require('web.ajax');

    publicWidget.registry.car_garage = publicWidget.Widget.extend({
        selector : '.car_garage',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_garage_car', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});