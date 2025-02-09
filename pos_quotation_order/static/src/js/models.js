/* Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
   Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('pos_quotation_order.models', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var models = require('point_of_sale.models');
    var session = require('web.session');
    var QWeb = core.qweb;
    var _t = core._t;

    models.load_models({
        model:  'pos.quotation',
        fields: ['name', 'partner_id', 'date_order', 'amount_total', 'lines', 'state'],
        domain: [['state', '=', 'draft']],
        loaded: function (self, quotations) {
            self.quotations = quotations;
        }
    });

    models.load_models({
        model:  'pos.quotation.line',
        fields: ['product_id', 'qty'],
        loaded: function (self, quotation_lines) {
            self.quotation_lines = quotation_lines;
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.quotation_ref = this.quotation_ref;
            return data;
        },
        init_from_JSON: function (json) {
            this.quotation_ref = json.quotation_ref;
            _super_order.init_from_JSON.call(this, json);
        },
    });

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _save_to_server: function (orders, options) {
            var self = this;
            return posmodel_super._save_to_server.apply(this, arguments).then(function (server_ids) {
                _.each(orders, function (o) {
                    if (o.data.quotation_ref) {
                        var index = self.quotations.indexOf(o.data.quotation_ref);
                        self.quotations.splice(index, 1);
                    }
                });
            });
        }
    });
});
