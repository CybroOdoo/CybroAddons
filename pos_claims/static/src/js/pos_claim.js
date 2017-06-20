odoo.define('point_of_sale.pos_claims', function (require) {
"use strict";
var chrome = require('point_of_sale.chrome');
var db = require('point_of_sale.DB');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var Model = require('web.DataModel');
var popup = require('point_of_sale.popups');
var Model = require('web.DataModel');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;

models.load_models({
    model: 'pos.order',
    fields: ['name', 'lines', 'partner_id'],
    loaded: function(self,claim_orders){
        self.order = [];
        for (var i = 0; i < claim_orders.length; i++) {
            self.order[i] = claim_orders[i];
        }
    },
});

models.load_models({
    model: 'res.partner',
    fields: ['name', 'id', 'email'],
    loaded: function(self,claim_customers){
        self.customer = [];
        for (var i = 0; i < claim_customers.length; i++) {
            self.customer[i] = claim_customers[i];
        }
    },
});

models.load_models({
    model: 'pos.order.line',
    fields: ['product_id','qty'],
    loaded: function(self,claim_products){
    self.order_line = [];
    for (var i = 0; i < claim_products.length; i++) {
        self.order_line[i] = claim_products[i];
    }
    },
});

chrome.Chrome.include({
    events: {
            "click .pos-claims": "on_click_pos_claims",
        },
    renderElement: function(){
        var self = this;
        return this._super();
    },
     on_click_pos_claims: function () {
        var list =[];
        var list1 =[];
        for (var i = 0; i < this.pos.order.length; i++) {
            var orders = this.pos.order[i];
            if (orders.name){
                list.push({
                    'label': orders.name,
                    'id':orders.id,
                    });
            }
        }
         for (var i = 0; i < this.pos.customer.length; i++) {
            var customers = this.pos.customer[i];
            if (customers.name){
                list1.push({
                    'label': customers.name,
                    'id':customers.id,
                    });
            }
        }
        this.gui.show_popup('pos_claim',{orders:list, customers:list1});
    },
});

var PosClaimWidget = popup.extend({
    template:'PosClaimWidget',
    events : {
            'click .selected_order': 'on_click_select_order',
            'click .selected_customer': 'on_click_select_customer',
            'click .button.confirm': 'click_confirm',
            'click .button.cancel':  'click_cancel',
        },
    show : function(options){
        options = options || [];
        var self = this;
        this._super(options);
        this.orders = options.orders || [];
        this.customers = options.customers || [];
        this.product = options.product || [];
        this.renderElement();
        },

    on_click_select_order:function(){
    var selected_order = $('.selected_order').val();
    for (var i = 0; i < this.pos.order.length; i++) {
        if (this.pos.order[i].id==selected_order){
            var orders = this.pos.order[i];
        }
    }
    if (orders) {
        var x = document.getElementsByClassName('selected_customer');
        x[0].selectedIndex = orders.partner_id[0];
        if (orders.partner_id)
        {
            for (var i = 0; i < this.pos.customer.length; i++) {
            if (this.pos.customer[i].id==orders.partner_id[0]){
                var customers = this.pos.customer[i];
                }
            }
            if (customers)
            {
                var x = document.getElementsByClassName('select_email');
                x[0].value = customers.email;
            }
        }
    }
    var product = [];
        if (orders)
        {
            for (var i = 0; i < this.pos.order_line.length; i++){
            for (var j = 0; j < orders.lines.length; j++){
                if (this.pos.order_line[i].id == orders.lines[j]){
                var product_line = this.pos.order_line[i];
                if (product_line.product_id){
                    product.push({
                        'label': product_line.product_id[1],
                        'id':product_line.id,
                        });
                    }
                }
            }
         }
            this.$('.selected_product').html(QWeb.render('PosClaimProductWidget',{product:product}));
        }
    },

    on_click_select_customer:function() {
        var selected_customer = $('.selected_customer').val();
        for (var i = 0; i < this.pos.customer.length; i++) {
        if (this.pos.customer[i].id==selected_customer){
            var customers = this.pos.customer[i];
            }
        }
        if (customers)
        {
            var x = document.getElementsByClassName('select_email');
            x[0].value = customers.email;
        }
    },
    
   click_confirm: function(){
        var self   = this;
        var fields = {};
        this.$('.popup .detail').each(function(idx,el){
        fields[el.name] = el.value;
        });
        if (fields.partner_id && fields.claim_product) {
            new Model('pos.claims').call('create_from_ui', [fields]);
            this.gui.close_popup();
        }
       else{
            alert('You need to specify the Product and Customer')
        }
    },

   click_cancel: function(){
        this.gui.close_popup();
        if (this.options.cancel) {
            this.options.cancel.call(this);
        }
    },

   renderElement: function(){
        var self = this;
        return this._super();
    },
});
gui.define_popup({name:'pos_claim', widget: PosClaimWidget});
});
