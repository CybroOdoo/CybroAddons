odoo.define('product_return_pos.models',function(require) {
    "use strict";



var models = require('point_of_sale.models');
var gui = require('point_of_sale.Gui');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t  = require('web.core')._t;
var session = require('web.session');



models.load_models({
    model:  'pos.order',
    fields: ['name', 'partner_id','date_order','amount_total', 'amount_tax',
        'pos_reference','lines','state','session_id','company_id','return_ref','return_status'],
    loaded: function(self, orders){

        self.orders = orders;
        }
    },
    {
    model: 'pos.order.line',
    fields: ['product_id','qty','price_unit','price_subtotal_incl','order_id','discount','returned_qty'],
    loaded: function(self,order_lines){

    self.order_line = [];
    for (var i = 0; i < order_lines.length; i++) {
        self.order_line[i] = order_lines[i];
    }
    }
});








var _super_orderline = models.Orderline;
models.Orderline = models.Orderline.extend({

    set_line_id: function(line_id){
        this.line_id = line_id;
    },
    export_as_JSON: function(){
        var json = _super_orderline.prototype.export_as_JSON.apply(this,arguments);
        json.line_id = this.line_id;
        return json;
    },
    init_from_JSON: function(json){
        _super_orderline.prototype.init_from_JSON.apply(this,arguments);
        this.line_id = json.line_id;
    },
});

var _super = models.Order;
models.Order = models.Order.extend({

    add_product: function (product, options) {


        var order    = this.pos.get_order();
        _super.prototype.add_product.call(this, product, options);
        if (options !== undefined) {
            if (options.extras !== undefined) {
                for (var prop in options.extras) {
                    if (prop === 'return_ref') {
                        this.return_ref = options.extras['return_ref']
                        this.trigger('change', this);
                    }
                    if (prop === 'label') {
                        order.selected_orderline.set_line_id(options.extras['label']);
                    }

                }

            }

        }

    },

    export_as_JSON: function(){
        var json = _super.prototype.export_as_JSON.apply(this,arguments);
        json.return_ref = this.return_ref;
        return json;
    },
    init_from_JSON: function(json){
        _super.prototype.init_from_JSON.apply(this,arguments);
        this.return_ref = json.return_ref;
    }

});

models.PosModel.extend({
    _save_to_server: function (orders, options) {
        if (!orders || !orders.length) {
            var result = $.Deferred();
            result.resolve([]);
            return result;
        }
        var fields = _.find(this.models,function(model){ return model.model === 'pos.order'; }).fields;
        options = options || {};

        var self = this;
        var timeout = typeof options.timeout === 'number' ? options.timeout : 7500 * orders.length;

        // Keep the order ids that are about to be sent to the
        // backend. In between create_from_ui and the success callback
        // new orders may have been added to it.
        var order_ids_to_sync = _.pluck(orders, 'id');

        // we try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
        // then we want to notify the user that we are waiting on something )
        var args = [_.map(orders, function (order) {
                order.to_invoice = options.to_invoice || false;
                return order;
            })];
        return rpc.query({
                model: 'pos.order',
                method: 'create_from_ui',
                args: args,
                kwargs: {context: session.user_context},
            }, {
                timeout: timeout,
                shadow: !options.to_invoice
            })
            .then(function (server_ids) {
                _.each(order_ids_to_sync, function (order_id) {
                    self.db.remove_order(order_id);
                });
                self.set('failed',false);
                if (server_ids.length != 0){
                    for (var item in server_ids){
                        rpc.query({
                            model: 'pos.order',
                            method: 'search_read',
                            args: [[['id', '=', server_ids[item]]], fields],
                            limit: 1,
                        })
                        .then(function (order){
                            self.orders.unshift(order[0]);
                        });
                    }
                }
                self.load_server_data();
                return server_ids;
            }).catch(function (type, error){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    //if warning do not need to display traceback!!
                    if (error.data.exception_type == 'warning') {
                        delete error.data.debug;
                    }

                    // Hide error if already shown before ...
                    if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                        this.showpopup('error-traceback',{
                            'title': error.data.message,
                            'body':  error.data.debug
                        });
                    }
                    self.set('failed',error);
                }
                console.error('Failed to send orders:', orders);
            });
    },
});





});