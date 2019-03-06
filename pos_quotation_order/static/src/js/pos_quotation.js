odoo.define('point_of_sale.pos_quotation_order', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var rpc = require('web.rpc');
var PopupWidget = require('point_of_sale.popups');
var ProductListWidget = screens.ProductListWidget;
var ScreenWidget = screens.ScreenWidget;
var QWeb = core.qweb;
var _t = core._t;

var QuotationPopupWidget = PopupWidget.extend({
    template: 'QuotationPopupWidget',
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
        var new_quotation = [];
        var fields = _.find(this.pos.models,function(model){ return model.model === 'pos.quotation'; }).fields;
        var line_fields = _.find(this.pos.models,function(model){ return model.model === 'pos.quotation.line'; }).fields;
        var today = new Date().toJSON().slice(0,10);
        var order = this.pos.get_order();
        var order_to_save = order.export_as_JSON();
        var order_lines = this.pos.get_order().get_orderlines();
        var order_date = this.$('.order_date').val();
        var order_note = this.$('.order_note').val();
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
        $('.alert_msg').text("");
        if (order_date && order_date < today || valid_date==false || !order_date){
            $('.alert_msg').text("Please Select Valid Order Date!");
        }
        else{
            $('.alert_msg').text("");
            if (order_date){
                order_to_save.date_order = order_date;
                }
            order_to_save.note = order_note;
            rpc.query({
                model: 'pos.quotation',
                method: 'create_from_ui',
                args: [order_to_save],
            })
            .then(function(order){
                rpc.query({
                    model: 'pos.quotation',
                    method: 'search_read',
                    args: [[['id', '=', order['id']]], fields],
                    limit: 1,
                })
                .then(function (quotation){
                    self.pos.quotations.push(quotation[0]);
                     for (var line in quotation[0]['lines']){
                        rpc.query({
                            model: 'pos.quotation.line',
                            method: 'search_read',
                            args: [[['id', '=', quotation[0]['lines'][line]]], line_fields],
                            limit: 1,
                        }).then(function (quotation_line){
                        console.log(quotation_line);
                        self.pos.quotation_lines.push(quotation_line[0]);
                    });
                }
            });
            self.gui.close_popup();
            self.pos.delete_current_order();
            self.gui.show_popup('pos_quot_result',{
            'body': _t('Quotation Ref : ')+ order['name'] ,
            });
        });
    }
    },

});
//
//var paymentscreen = screens.PaymentScreenWidget.extend({
//    template: 'paymentscreen',
//    click_set_customer: function(){
//        console.log("hhh")
//        this.gui.show_screen('clientlist');
//    },
//});

var QuotationListScreenWidget = ScreenWidget.extend({
    template: 'QuotationListScreenWidget',
    back_screen:   'product',
    init: function(parent, options){
        var self = this;
        this._super(parent, options);
    },

    show: function(){
        var self = this;
        this._super();
        this.renderElement();
        this.$('.back').click(function(){
            self.gui.back();
        });

        var quotations = this.pos.quotations;
        this.render_list(quotations);

         this.$('.quotation-list-contents').delegate('.quotation-line .confirm_quotation','click',function(event){
            self.line_select(event,$(this.parentElement.parentElement),parseInt($(this.parentElement.parentElement).data('id')));
        });

        var search_timeout = null;

        if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
            this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
        }

        this.$('.searchbox input').on('keyup',function(event){
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

    render_list: function(quotations){
        var contents = this.$el[0].querySelector('.quotation-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(quotations.length,1000); i < len; i++){
            var quotation    = quotations[i];
            var quotation_line_html = QWeb.render('QuotationLine',{widget: this, quotation:quotations[i]});
            var quotation_line = document.createElement('tbody');
            quotation_line.innerHTML = quotation_line_html;
            quotation_line = quotation_line.childNodes[1];
            contents.appendChild(quotation_line);
        }
    },

    line_select: function(event,$line,id){
        var self = this;
        var order = this.pos.get_order();
        for (var quot_id in this.pos.quotations){
            if (this.pos.quotations[quot_id]['id'] == id){
                var selected_quotation = this.pos.quotations[quot_id]
            }
        }
        if (selected_quotation){
            for (var line in this.pos.quotation_lines){
                if (selected_quotation['lines'].indexOf(this.pos.quotation_lines[line]['id']) > -1 ){
                var product_id = this.pos.db.get_product_by_id(this.pos.quotation_lines[line]['product_id'][0]);
                this.pos.get_order().add_product(product_id,{ quantity: this.pos.quotation_lines[line]['qty']});
                }
            }
            order.quotation_ref = selected_quotation;
            if (selected_quotation.partner_id){
                var partner = this.pos.db.get_partner_by_id(selected_quotation.partner_id[0]);
                order.set_client(partner);
            }
            this.gui.show_screen('products');
        }

    },

    perform_search: function(query, associate_result){
        var quotations;
        if(query){
            quotations = this.search_quotation(query);
            this.render_list(quotations);
        }else{
            quotations = this.pos.quotations;
            this.render_list(quotations);
        }
    },
    clear_search: function(){
        var quotations = this.pos.quotations;
        this.render_list(quotations);
        this.$('.searchbox input')[0].value = '';
        this.$('.searchbox input').focus();
    },

    search_quotation: function(query){
        try {
            var re = RegExp(query);
        }catch(e){
            return [];
        }
        var results = [];
        for (var quot_id in this.pos.quotations){
            var r = re.exec(this.pos.quotations[quot_id]['name']);
            if(r){
            results.push(this.pos.quotations[quot_id]);
            }
        }
        return results;
    },
});


gui.define_popup({name:'pos_quot', widget: QuotationPopupWidget});

var QuotationResultPopupWidget = PopupWidget.extend({
    template: 'QuotationResultPopupWidget',
});

gui.define_popup({name:'pos_quot_result', widget: QuotationResultPopupWidget});
gui.define_screen({name:'quotation_list', widget: QuotationListScreenWidget});

var QuotationListButton = screens.ActionButtonWidget.extend({
    template: 'QuotationListButton',
    button_click: function(){
        this.gui.show_screen('quotation_list');
    }
});

screens.define_action_button({
    'name': 'pos_quotation_list',
    'widget': QuotationListButton,
    'condition': function () {
        return this.pos.config.enable_quotation;
    }
});


var QuotationButton = screens.ActionButtonWidget.extend({
    template: 'QuotationButton',
    button_click: function(){
        var order_lines = this.pos.get_order().get_orderlines();
        var flag_negative = false;
        for (var line in order_lines){
            if (order_lines[line].quantity < 0){
                flag_negative = true;
            }
        }
        if(this.pos.get_order().get_orderlines().length > 0 && flag_negative == false && this.pos.get_order().get_total_with_tax()>0){
            this.gui.show_popup('pos_quot');
        }
        else if(flag_negative == true){
            this.gui.show_popup('pos_quot_result',{
                'body': _t('Invalid Order: Negative Quantity is Not Allowed'),
            });
        }
        else if(this.pos.get_order().get_orderlines().length == 0 || this.pos.get_order().get_total_with_tax() <=0){
            this.gui.show_popup('pos_quot_result',{
            'body': _t('Invalid Order : Please Add Some Order Lines'),
            });
        }
    },
});

screens.define_action_button({
    'name': 'pos_quotation_order',
    'widget': QuotationButton,
    'condition': function () {
        return this.pos.config.enable_quotation;
    }
});

});

