odoo.define('odoo_website_helpdesk.multiple_product_choose', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var publicWidget = require('web.public.widget');
    publicWidget.registry.SelectProduct = publicWidget.Widget.extend({
        selector: '.website_ticket',
        start: function () {
            var self = this;
            rpc.query({
                route: '/product'
            }).then(function (res) {
                var ar = res;
                self.$el.find('#product').empty();
                ar.forEach(function (item) {
                    self.$el.find('#product').append("<option value='" + item.id + "'>" + item.name + "</option>");
                });
                self.$el.find('#product').SumoSelect({ clearAll: true });
            });
            return this._super.apply(this, arguments);
        },
        });
     return publicWidget.registry.SelectProduct;
});
