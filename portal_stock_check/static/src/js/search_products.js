odoo.define('portal_Stock_check.portal_product_availability', function (require) {
    'use strict';
var publicWidget = require('web.public.widget');
var core = require('web.core');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');


publicWidget.registry.SearchBar = publicWidget.Widget.extend({
     selector: '.o_website_product_search',

     events: {
        'keyup .o_portal_product_input': '_product_search',
    },
    init: function () {
            this._super.apply(this, arguments);
    },
    _product_search: function (ev) {
        var product_name = $('#product_name_input').val();
        ajax.jsonRpc("/product/search", 'call', {
                'name' : product_name
        }).then(function (result) {
            if (result != 'false'){
                 $('.product_results_table').html(QWeb.render('productSearch',{'result':result}));
            }
        })
    }
    })
})


