odoo.define('pos_quotation_order.models', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var models = require('point_of_sale.models');
var Model = require('web.DataModel');
var QWeb = core.qweb;
var _t = core._t;

models.load_models({
    model:  'pos.quotation',
    fields: ['name', 'partner_id','date_order','amount_total','lines','state'],
    domain: [['state','=','draft']],
    loaded: function(self, quotations){
        self.quotations = quotations;
        }
    });

    models.load_models({
    model:  'pos.quotation.line',
    fields: ['product_id', 'qty'],
    loaded: function(self, quotation_lines){
        self.quotation_lines = quotation_lines;
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.quotation_ref = this.quotation_ref;
            return data;
        },
        init_from_JSON: function(json) {
            this.quotation_ref = json.quotation_ref;
            _super_order.init_from_JSON.call(this, json);
        },
    });

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                var result = $.Deferred();
                result.resolve([]);
                return result;
            }

            options = options || {};

            var self = this;
            var timeout = typeof options.timeout === 'number' ? options.timeout : 7500 * orders.length;
            var order_ids_to_sync = _.pluck(orders, 'id');
            var quot_model = new Model('pos.quotation');
            var fields = _.find(this.models,function(model){ return model.model === 'pos.quotation'; }).fields;
            var posOrderModel = new Model('pos.order');
            return posOrderModel.call('create_from_ui',
                [_.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                })],
                undefined,
                {
                    shadow: !options.to_invoice,
                    timeout: timeout
                }
            ).then(function (server_ids) {
                if (server_ids[1].length != 0){
                    for (var item in server_ids[1]){
                        quot_model.query(fields).filter([['id','=',server_ids[1][item]]]).first().then(function(quotation){
                        var index = self.quotations.indexOf(quotation);
                        self.quotations.splice(index, 1);
                        });
                    }
                }
                _.each(order_ids_to_sync, function (order_id) {
                    self.db.remove_order(order_id);
                });
                self.set('failed',false);
                return server_ids[0];
            }).fail(function (error, event){
                if(error.code === 200 ){
                    if (error.data.exception_type == 'warning') {
                        delete error.data.debug;
                    }
                    if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                        self.gui.show_popup('error-traceback',{
                            'title': error.data.message,
                            'body':  error.data.debug
                        });
                    }
                    self.set('failed',error)
                }
                event.preventDefault();
                console.error('Failed to send orders:', orders);
            });
        },
    });

});