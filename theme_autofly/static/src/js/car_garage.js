odoo.define('theme_autofly.car_garage', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');
    const { qweb } = require('web.core');
    var ajax = require('web.ajax');

    publicWidget.registry.car_garage = publicWidget.Widget.extend({
        selector : '.car_garage',
        /**Function for getting the garage details**/
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_garage_car', 'call', {})
            .then(function (data) {
                if(data){
                    self.$el.html(data);
                }
            });
        }
    });
});