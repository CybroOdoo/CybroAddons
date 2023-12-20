odoo.define('theme_autofly.all_type', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const { qweb } = require('web.core');
    var ajax = require('web.ajax');

    publicWidget.registry.all_type = publicWidget.Widget.extend({
        selector : '.all_type',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_all_type', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});