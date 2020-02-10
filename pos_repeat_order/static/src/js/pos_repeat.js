
odoo.define('pos_repeat_order.repeat',function(require) {
    "use strict";

var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
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
        'pos_reference','lines','state','session_id','company_id'],
    loaded: function(self, orders){
        self.orders = orders;
        }
    });

    var RepeatButton = screens.ActionButtonWidget.extend({
    template: 'RepeatButton',
    button_click: function(){
        var orders = this.pos.orders;
        this.gui.show_screen('orderlist',{orders:orders});

    }
});
screens.ProductScreenWidget.include({
    start: function(){
    this._super();
    this.coupons = new RepeatButton(this,{});
    this.coupons.replace(this.$('.placeholder-RepeatButton'));
    },
    button_click: function(){
    var orders = this.pos.orders;

    }
});


var RepeatWidget = PopupWidget.extend({
    template:'RepeatWidget',

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
                    rows += "<tr><td>" + id + "</td><td>" + price_unit +" </td><td>" + name + "</td><td>" + qty + "</td><td>" + discount + "</td><td>";
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
            }).catch(function () {
                alert("NO DATA")
            });
    },
    click_confirm: function(){
       console.log("vonfirm")
        var self = this;
	    var myTable = document.getElementById('list').tBodies[0];
        var count  = 0;
        var c = 1;

        for (r=0, n = myTable.rows.length; r < n; r++) {
            var row = myTable.rows[r]
            var ordered_qty = document.getElementById("text"+c).value
            if (row.cells[3].innerHTML < ordered_qty){
                count +=1
            }
            c = c+1
        }
            c = 1;
            // OrderSuper.prototype.set_client.call(this, this.client);
            for (var r=0, n = myTable.rows.length; r < n; r++) {
                row = myTable.rows[r]
                ordered_qty = document.getElementById("text"+c).value;
                var product   = this.pos.db.get_product_by_id(row.cells[0].innerHTML);
                if (!product) {
                    return;
                }

                if (ordered_qty > 0){
                    this.pos.get_order().add_product(product, {
                    price: row.cells[1].innerHTML,
                    quantity: (ordered_qty),
                    discount:row.cells[4].innerHTML,
                    merge: false,

                    });

                }
                c = c+1

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
gui.define_popup({name:'RepeatWidget', widget: RepeatWidget});
var OrderListScreenWidget = screens.ScreenWidget.extend({
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
        this.$('.repeat_order').click(function(e){
            var order = $(e.target).closest("tr").data('id');
            self.repeat_order(order);
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
        if (this.pos.get_client())
        {
        for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
            if(orders[i].partner_id[0] == this.pos.get_client().id){
                var order    = orders[i];
                var orderline_html = QWeb.render('OrderLine',{widget: this, order:order});
                var orderline = document.createElement('tbody');
                orderline.innerHTML = orderline_html;
                orderline = orderline.childNodes[1];
                contents.appendChild(orderline);
        }
        }
        }
        else{ alert("Please select a customer") }

    },
    repeat_order:function(order_id){
        var self = this;
        var order = this.get_order_by_id(order_id);
        var client = ''
        if (order.partner_id){
             client = order.partner_id[0];
             self.gui.show_popup('RepeatWidget',{ref: order.pos_reference,client:client});
        }


    },
    get_order_by_id: function(id){
        var orders = this.pos.orders;
        for (var i in orders){
            if (orders[i].id === id){
                console.log("orders[i]",orders[i])
                return orders[i];
            }
        }

    }
    });
gui.define_screen({name:'orderlist', widget: OrderListScreenWidget});

});



