odoo.define('low_stock_alert', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');
var pyUtils = require('web.py_utils');


//import ListRenderer from 'web.ListRenderer';
//import pyUtils from 'web.py_utils';

    ListRenderer.include({

        _renderBodyCell: function (record, node) {
            var $td = this._super.apply(this, arguments);
            console.log('this', this)
            console.log('arguments', arguments)

            if (node.tag !== 'field') {
                return $td;
            }

            if (arguments && arguments[0] && arguments[0]['model'] == 'product.template') {
                if (arguments[0]['data'] && arguments[0]['data']['alert_state'] && arguments[0]['data']['alert_state'] == true) {
                    $td.css({'color': '#000000', 'background-color': 'rgba(253, 198, 198, 0.39)'});
                }
            }



            return $td;
        },

    });
});




