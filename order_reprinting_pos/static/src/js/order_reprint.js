odoo.define('order_reprinting_pos',function(require) {
"use strict";

var gui = require('point_of_sale.gui');
var chrome = require('point_of_sale.chrome');
var popups = require('point_of_sale.popups');
var core = require('web.core');
var models = require('point_of_sale.models');
var PosModelSuper = models.PosModel;
var pos_screens = require('point_of_sale.screens');
var Model = require('web.DataModel');
var QWeb = core.qweb;
var _t = core._t;

models.load_models({
            model: 'pos.order',
            fields: ['id', 'name', 'session_id', 'pos_reference', 'partner_id', 'amount_total', 'amount_tax'],
            loaded: function (self, pos_orders) {
                var new_order_list = [];
                for (var i in pos_orders){
                    new_order_list[pos_orders[i].id] = pos_orders[i];
                }
                self.pos_orders = new_order_list;
            },
        });

var DomCache = core.Class.extend({
        init: function(options){
            options = options || {};
            this.max_size = options.max_size || 2000;

            this.cache = {};
            this.access_time = {};
            this.size = 0;
        },
        cache_node: function(key,node){
            var cached = this.cache[key];
            this.cache[key] = node;
            this.access_time[key] = new Date().getTime();
            if(!cached){
                this.size++;
                while(this.size >= this.max_size){
                    var oldest_key = null;
                    var oldest_time = new Date().getTime();
                    for(key in this.cache){
                        var time = this.access_time[key];
                        if(time <= oldest_time){
                            oldest_time = time;
                            oldest_key  = key;
                        }
                    }
                    if(oldest_key){
                        delete this.cache[oldest_key];
                        delete this.access_time[oldest_key];
                    }
                    this.size--;
                }
            }
            return node;
        },
        clear_node: function(key) {
            var cached = this.cache[key];
            if (cached) {
                delete this.cache[key];
                delete this.access_time[key];
                this.size --;
            }
        },
        get_node: function(key){
            var cached = this.cache[key];
            if(cached){
                this.access_time[key] = new Date().getTime();
            }
            return cached;
        },
    });
chrome.OrderSelectorWidget.include({
    renderElement: function(){
        var self = this;
        this._super();
        this.$('.orders-list').click(function(event){
            self.gui.show_screen('OldOrdersWidget');
        });
    },
});

models.PosModel = models.PosModel.extend({
    _save_to_server: function (orders, options) {
        var result_new = PosModelSuper.prototype._save_to_server.call(this, orders, options);
        var self = this;
        var new_order = {};
        var order_list = self.pos_orders;
        for (var i in orders) {
            var partners = self.partners;
            var partner = "";
            for(var j in partners){
                if(partners[j].id == orders[i].data.partner_id){
                    partner = partners[j].name;
                }
            }
            new_order = {
                'amount_tax': orders[i].data.amount_tax,
                'amount_total': orders[i].data.amount_total,
                'pos_reference': orders[i].data.name,
                'partner_id': [orders[i].data.partner_id, partner],
                'session_id': [
                    self.pos_session.id, self.pos_session.name
                ]
            };
            order_list.push(new_order);
            self.pos_orders = order_list;
            self.gui.screen_instances.OldOrdersWidget.render_list(order_list);
        }
        return result_new;
    },
});

var OldOrdersWidget = pos_screens.ScreenWidget.extend({
    template: 'OldOrdersWidget',

    init: function(parent, options){
        this._super(parent, options);
        this.order_cache = new DomCache();
        this.order_string = "";
        this.pos_reference = "";
    },

    auto_back: true,
    renderElement: function () {
        this._super(this);
        var self = this;
        this.$('.button.print').click(function(){
            if (!self._locked) {
                self.gui.screen_instances.receipt.print();
            }
            new Model('pos.order').call('get_details',[self.pos_reference]).then(function(id){
                self.chrome.do_action('order_reprinting_pos.pos_receipt_report',{additional_context:{
                    active_ids:[id],
                }});
            });
        });
    },

    show: function(){
        var self = this;
        this._super();

        this.renderElement();
        this.details_visible = false;

        this.$('.back').click(function(){
            self.gui.back();
        });
        var pos_orders = this.pos.pos_orders;
        this.render_list(pos_orders);


        var search_timeout = null;

        if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
            this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
        }

        this.$('.searchbox input').on('keypress',function(event){
            clearTimeout(search_timeout);

            var query = this.value;
            search_timeout = setTimeout(function(){
                self.perform_search(query,event.which === 13);
            },70);
        });

        this.$('.searchbox .search-clear').click(function(){
            self.clear_search();
        });
    },
    hide: function () {
        this._super();
        this.new_client = null;
    },
    perform_search: function(query, associate_result){
        var new_orders;
        if(query){
            new_orders = this.search_order(query);

            this.render_list(new_orders);
        }else{
            var orders = this.pos.pos_orders;
            this.render_list(orders);
        }
    },
    search_order: function(query){
        var self = this;
        try {
            query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
            query = query.replace(' ','.+');
            var re = RegExp("([0-9]+):.*?"+query,"gi");
        }catch(e){
            return [];
        }
        var results = [];
        for(var i = 0; i < Math.min(self.pos.pos_orders.length,1000); i++){
            var r = re.exec(this.order_string);
            if(r){
                var id = Number(r[1]);
                results.push(this.get_order_by_id(id));
            }else{
                break;
            }
        }
        return results;
    },
    // returns the order with the id provided
    get_order_by_id: function (id) {
        return this.pos.pos_orders[id];
    },
    clear_search: function(){
        var orders = this.pos.pos_orders;
        this.render_list(orders);
        this.$('.searchbox input')[0].value = '';
        this.$('.searchbox input').focus();
    },
    render_list: function(orders){
        var self = this;
        for(var i = 0, len = Math.min(orders.length,1000); i < len; i++) {
            if (orders[i]) {
                var order = orders[i];
                self.order_string += i + ':' + order.pos_reference + '\n';
            }
        }

        this.$('.order-list-contents').delegate('.print-button','click',function(event){
            var pos_ref = $(this).data('id');
            var order_new = null;
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++) {
                if (orders[i] && orders[i].pos_reference == pos_ref) {
                    order_new = orders[i];
                }
            }
            $('span.searchbox').css('display', 'none');
            $('.button.print').css('display', 'block');
            var lines = [];
            var payments = [];
            var discount = 0;
            new Model('pos.order').call('get_orderlines',[order_new.pos_reference]).then(function(result){
                lines = result[0];
                payments = result[2];
                discount = result[1];
                self.gui.show_screen('OldOrdersWidget');
                self.$('.window').html(QWeb.render('PosTicketOld',{
                    widget:self,
                    order: order_new,
                    change: result[3],
                    orderlines: lines,
                    discount_total: discount,
                    paymentlines: payments,
                }));
                self.pos_reference = order_new.pos_reference;
            });
        });
        
        var contents = this.$el[0].querySelector('.order-list-contents');
        if (contents){
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++) {
                if (orders[i]) {
                    var order = orders[i];

                    var orderline = this.order_cache.get_node(order.id);
                    if (!orderline) {
                        var clientline_html = QWeb.render('OrderLine', {widget: this, order: order});
                        var orderline = document.createElement('tbody');
                        orderline.innerHTML = clientline_html;
                        orderline = orderline.childNodes[1];
                        if (order.id){
                            this.order_cache.cache_node(order.id, orderline);
                        }
                        else{
                            this.order_cache.cache_node(i, orderline);
                        }
                    }
                    contents.appendChild(orderline);
                }
            }
        }
    },
    
    close: function(){
        this._super();
    },
});
gui.define_screen({name:'OldOrdersWidget', widget: OldOrdersWidget});


});