odoo.define('theme_autofly.service_product', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const { qweb } = require('web.core');
    var ajax = require('web.ajax');

    publicWidget.registry.service_product = publicWidget.Widget.extend({
        selector : '.product_service',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_service_product', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});