odoo.define('point_of_sale.pos_sales_orders', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var Model = require('web.DataModel');
var core = require('web.core');
var PopupWidget = require('point_of_sale.popups');
var ProductListWidget = screens.ProductListWidget;
var QWeb = core.qweb;
var _t = core._t;

var SaleOrderButton = screens.ActionButtonWidget.extend({
    template: 'SaleOrderButton',
    button_click: function(){
        var order_lines = this.pos.get_order().get_orderlines();
        var flag_negative = false;
        for (var line in order_lines){
            if (order_lines[line].quantity < 0){
                flag_negative = true;
            }
        }
        if(this.pos.get_order().get_orderlines().length > 0 && this.pos.get_client() && flag_negative == false && this.pos.get_order().get_total_with_tax()>0){
            this.gui.show_popup('pos_so');
        }
        else if(flag_negative == true){
            this.gui.show_popup('alert',{
                'title': _t('Alert: Invalid Order'),
                'body': _t('Negative Quantity is Not Allowed'),
            });
        }
        else if(this.pos.get_order().get_orderlines().length == 0 || this.pos.get_order().get_total_with_tax() <=0){
            this.gui.show_popup('alert',{
            'title': _t('Alert: Invalid Order'),
            'body': _t('Please Add Some Order Lines'),
            });
        }
        else{
            this.gui.show_popup('alert',{
                'title': _t('Alert: Invalid Customer'),
                'body': _t('Please Select Customer'),
            });
        }
    },
});

screens.define_action_button({
    'name': 'pos_sale_order',
    'widget': SaleOrderButton,
});

var SaleOrderPopupWidget = PopupWidget.extend({
    template: 'SaleOrderPopupWidget',
    events: _.extend({}, PopupWidget.prototype.events,{
        "keyup .order_date" : "date_validate",
    }),
    show: function(options){
        options = options || {};
        var self = this;
        this._super(options);
        this.renderElement();
    },
    date_validate: function(){
        var v = $(".order_date").val();
        if (v.match(/^\d{4}$/) !== null) {
            $(".order_date").val(v + '/');
            }
        else if (v.match(/^\d{4}\/\d{2}$/) !== null) {
            $(".order_date").val(v + '/');
            }
        },
    click_confirm: function(){
        var self = this;
        var sale_order = {};
        var today = new Date().toJSON().slice(0,10);
        var order = this.pos.get_order();
        var order_lines = this.pos.get_order().get_orderlines();
        var order_date = this.$('.order_date').val();
        var valid_date = true;
        var validatePattern = /^(\d{4})([/|-])(\d{1,2})([/|-])(\d{1,2})$/;
        if (order_date){
            var dateValues = order_date.match(validatePattern);
            if (dateValues == null){
                valid_date = false;
            }
            else{
                var orderYear = dateValues[1];
                var orderMonth = dateValues[3];
                var orderDate =  dateValues[5];
                if ((orderMonth < 1) || (orderMonth > 12)) {
                    valid_date = false;
                }
                else if ((orderDate < 1) || (orderDate> 31)) {
                    valid_date = false;
                }
                else if ((orderMonth==4 || orderMonth==6 || orderMonth==9 || orderMonth==11) && orderDate ==31) {
                    valid_date = false;
                }
                else if (orderMonth == 2){
                    var isleap = (orderYear % 4 == 0 && (orderYear % 100 != 0 || orderYear % 400 == 0));
                    if (orderDate> 29 || (orderDate ==29 && !isleap)){
                        valid_date = false;
                    }
                }
                var dates = [orderYear,orderMonth,orderDate];
                order_date = dates.join('-');
            }
        }
        sale_order.order_line = [];
        $('.alert_msg').text("");
        if (order_date && order_date < today || valid_date==false){
            $('.alert_msg').text("Please Select Valid Order Date!");
        }
        else{
            $('.alert_msg').text("");
            for (var line in order_lines){
                if (order_lines[line].quantity>0)
                {
                    var sale_order_line = [0,false,{product_id:null,product_uom_qty:0}]
                    sale_order_line[2].product_id = order_lines[line].product.id;
                    sale_order_line[2].product_uom_qty = order_lines[line].quantity;
                    sale_order.order_line.push(sale_order_line);
                }
            }
            sale_order.partner_id = this.pos.get_client().id;
            if (order_date){
                sale_order.validity_date = order_date;
                }
            sale_order.from_pos = true;
            var saleOrderModel = new Model('sale.order');
            saleOrderModel.call('create_from_ui',[sale_order]).then(function(order_ref){
                self.gui.close_popup();
                self.pos.delete_current_order();
                self.gui.show_popup('pos_so_ref',{
                'body': _t('Sale Order Ref : ')+ order_ref ,
                });
            });
        }
    }

});
gui.define_popup({name:'pos_so', widget: SaleOrderPopupWidget});

var SaleRefPopupWidget = PopupWidget.extend({
    template: 'SaleRefPopupWidget',
});

gui.define_popup({name:'pos_so_ref', widget: SaleRefPopupWidget});

});

