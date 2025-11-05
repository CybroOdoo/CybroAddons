odoo.define('product_return_pos.return',function(require) {
    "use strict";

var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var ScreenWidget = screens.ScreenWidget;
var gui = require('point_of_sale.gui');
var core = require('web.core');
var QWeb = core.qweb;
var PopupWidget = require('point_of_sale.popups');
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


var ReturnWidget = PopupWidget.extend({
    template:'ReturnWidget',

    init: function(parent, options){
        this._super(parent, options);
        this.options = {};
        this.pos_reference = "";

    },
    show: function(options){
        this._super(options);
        this.render_list(options);

    },
    events: {
        'click .button.cancel':  'click_cancel',
        'click .button.confirm': 'click_confirm',
    },
    render_list:function(options){
        $("#table-body").empty();
        var lines = [];
        this.pos_reference = options.ref
        rpc.query({
                model: 'pos.order',
                method: 'get_lines',
                args: [options.ref],
            }).then(function (result) {
                lines = result[0];
                for(var j=0;j < lines.length; j++){
                    var product_line = lines[j];
                    var rows = "";
                    var id = product_line.product_id
                    var price_unit = product_line.price_unit;
                    var name =product_line.product;
                    var qty = product_line.qty;
                    var line_id = product_line.line_id;
                    var discount = product_line.discount;
                    rows += "<tr><td>" + id + "</td><td>" + price_unit +" </td><td>" + name + "</td><td>" + qty + "</td><td>" + discount + "</td><td>" + line_id + "</td></tr>";
                    $(rows).appendTo("#list tbody");
                    var rows = document.getElementById('list').rows;
                    for (var row = 0; row < rows.length; row++) {
                        var cols = rows[row].cells;
                        cols[0].style.display = 'none';
                        cols[1].style.display = 'none';
                        cols[5].style.display = 'none';

                    }

                }
                var table = document.getElementById('list');
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {
                  var td = document.createElement('td');
                  var input = document.createElement('input');
                  input.setAttribute("type", "text");
                  input.setAttribute("value", 0);
                  input.setAttribute("id", "text"+i);
                  td.appendChild(input);
                  tr[i].appendChild(td);

                }
            }).fail(function () {
                alert("NO DATA")
            });
    },
    click_confirm: function(){

        var self = this;
	    var myTable = document.getElementById('list').tBodies[0];
        var count  = 0;
        var c = 1;

        for (r=0, n = myTable.rows.length; r < n; r++) {
            var row = myTable.rows[r]
            var return_qty = document.getElementById("text"+c).value
            if (row.cells[3].innerHTML < return_qty){
                count +=1
            }
            c = c+1
        }
        if (count > 0){
             alert('Please check the Returned Quantity,it is higher than purchased')
        }
        else{
            c = 1;
            // OrderSuper.prototype.set_client.call(this, this.client);
            for (var r=0, n = myTable.rows.length; r < n; r++) {
                row = myTable.rows[r]
                return_qty = document.getElementById("text"+c).value;
                var product   = this.pos.db.get_product_by_id(row.cells[0].innerHTML);
                if (!product) {
                    return;
                }

                if (return_qty > 0){
                    this.pos.get_order().add_product(product, {
                    price: row.cells[1].innerHTML,
                    quantity: -(return_qty),
                    discount:row.cells[4].innerHTML,
                    merge: false,
                    extras: {return_ref: this.pos_reference,
                            label:row.cells[5].innerHTML},
                    });

                }
                c = c+1

            }

            if (this.options.client){
                    this.pos.get_order().set_client(self.pos.db.get_partner_by_id(this.options.client));
            }

        }

        this.gui.close_popup();
        self.gui.show_screen('products');

    },
     click_cancel: function(){
        this.gui.close_popup();

    }

});
gui.define_popup({name:'ReturnWidget', widget: ReturnWidget});

var OrderListScreenWidget = ScreenWidget.extend({
        template:'OrderListScreenWidget',
    init: function(parent, options){
        this._super(parent, options);
    },
    show: function(){
        var self = this;
        this._super();
        this.renderElement();
        this.$('.back').click(function(){
            self.gui.back();
        });
        var orders = this.pos.orders;
        this.render_list(orders);
        var search_timeout = null;
        this.$('.searchbox input').on('keypress',function(event){
            clearTimeout(search_timeout);

            var searchbox = this;

            search_timeout = setTimeout(function(){
                self.perform_search(searchbox.value, event.which === 13);
            },70);
        });

        this.$('.searchbox .search-clear').click(function(){
            self.clear_search();
        });
        this.$('.return_order').click(function(e){
            var order = $(e.target).closest("tr").data('id');
            self.return_order(order);
        });
    },

    hide: function () {
        this._super();
    },
    get_orders: function(){
        return this.gui.get_current_screen_param('orders');
    },
    perform_search: function(query, associate_result){
        var orders;
        if(query){
            orders = this.search_order(query);
            this.render_list(orders);
        }else{
            orders = this.pos.orders;
            this.render_list(orders);
        }
    },
    search_order: function(query){
        try {
            var re = RegExp(query, 'i');
        }catch(e){
            return [];
        }
        var results = [];
        for (var order_id in this.pos.orders){
            var r = re.exec(this.pos.orders[order_id]['name']+ '|'+ this.pos.orders[order_id]['partner_id'][1]);
            if(r){
            results.push(this.pos.orders[order_id]);
            }
        }
        return results;
    },
    clear_search: function(){
        var orders = this.pos.orders;
        this.render_list(orders);
        this.$('.searchbox input')[0].value = '';
        this.$('.searchbox input').focus();
    },
    render_list: function(orders){
        var contents = this.$el[0].querySelector('.order-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
            var order    = orders[i];
            var orderline_html = QWeb.render('OrderLine',{widget: this, order:order});
            var orderline = document.createElement('tbody');
            orderline.innerHTML = orderline_html;
            orderline = orderline.childNodes[1];
            contents.appendChild(orderline);
        }
    },
    return_order:function(order_id){
        var self = this;
        var order = this.get_order_by_id(order_id);
        var client = ''
        if (order.partner_id){
             client = order.partner_id[0];
        }
        if (order && order.return_status ==='fully_return'){
                  self.gui.show_popup('error',_t('This is a fully returned order'));
        }
        else if (order && order.return_ref) {
            self.gui.show_popup('error',_t('This is a returned order'));
        }
        else{
            console.log(order.pos_reference,client)
            self.gui.show_popup('ReturnWidget',{ref: order.pos_reference,client:client});

        }

    },
    get_order_by_id: function(id){
        var orders = this.pos.orders;
        for (var i in orders){
            if (orders[i].id === id){
                return orders[i];
            }
        }

    }
});

gui.define_screen({name:'orderlist', widget: OrderListScreenWidget});
var ReturnButton = screens.ActionButtonWidget.extend({
    template: 'ReturnButton',
    button_click: function(){
        var orders = this.pos.orders;
        this.gui.show_screen('orderlist',{orders:orders});
    }
});

screens.define_action_button({
        'name': 'return',
        'widget': ReturnButton
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

models.PosModel = models.PosModel.extend({
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
            }).fail(function (type, error){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    //if warning do not need to display traceback!!
                    if (error.data.exception_type == 'warning') {
                        delete error.data.debug;
                    }

                    // Hide error if already shown before ...
                    if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                        self.gui.show_popup('error-traceback',{
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