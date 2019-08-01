odoo.define('pos_book_order.popups', function (require) {
"use strict";
    var core = require('web.core');
    var _t = core._t;
    var gui = require('point_of_sale.gui');
    var PopupWidget = require('point_of_sale.popups');
    var qweb = core.qweb;
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var pos_screens = require('point_of_sale.screens');
    var Widget = require('web.Widget');


var popup_widget = PopupWidget.extend({
    template: 'popup_widget',

    events: _.extend({}, PopupWidget.prototype.events,{
        'click .confirm': function(){
            var self = this;
            var new_quotation = [];
            var fields = _.find(this.pos.models,function(model){ return model.model === 'book.order'; }).fields;
            var line_fields = _.find(this.pos.models,function(model){ return model.model === 'book.order.line'; }).fields;
            var today = new Date().toJSON().slice(0,10);
            var order = this.pos.get_order();
            var so_val = order.export_as_JSON();
            var order_lines = this.pos.get_order().get_orderlines();
            var order_date = this.$('.order_date').val();
            var order_note = this.$('.order_note').val();
            var fields = {};
            self.$('.booking_field').each(function (idx, el) {
                fields[el.name] = el.value || false;
            });
            var value = {
                phone: fields['phone'],
                pickup_date: fields['pickup_date'],
                deliver_date: fields['deliver_date'],
                delivery_address: fields['delivery_address'],
                book_order: true
            };
            fields.options = value;
            var phone = fields.options.phone
            var pickup_date = fields.options.pickup_date
            var deliver_date = fields.options.deliver_date
            var delivery_address = fields.options.delivery_address
            var book_order = fields.options.book_order
            if (!pickup_date && !deliver_date ){
                 self.gui.show_popup('error',{
                                'title': _t('Date field is empty'),
                                'body': _t('Please select pickup or deliver date!!'),
                            });
            }
            else if(pickup_date && deliver_date ){
                 self.gui.show_popup('error',{
                                'title': _t('Select only one date (Deliver or Pickup date)'),
                            });
            }
            else if(pickup_date){
                if (pickup_date < today){
                    self.gui.show_popup('error',{
                                'title': _t('Please Select Valid Pickup Date!'),
                                'body': _t('Date must be greater than today'),
                            });
                    }
                else{
                    so_val.date_order = order_date;
                    so_val.note = order_note;
                    so_val.phone = phone;
                    so_val.pickup_date = pickup_date;
                    so_val.deliver_date = deliver_date;
                    so_val.delivery_address = delivery_address;
                    so_val.book_order = book_order;
                    rpc.query({
                        model: 'book.order',
                        method: 'create_from_ui',
                        args: [so_val],
                    })
                    .then(function(order){
                        rpc.query({
                            model: 'book.order',
                            method: 'search_read',
                            args: [[['id', '=', order['id']]], fields],
                            limit: 1,
                        })
                        .then(function (quotation){
                            self.pos.quotations.push(quotation[0]);
                             for (var line in quotation[0]['lines']){
                                rpc.query({
                                    model: 'book.order.line',
                                    method: 'search_read',
                                    args: [[['id', '=', quotation[0]['lines'][line]]], line_fields],
                                    limit: 1,
                                }).then(function (quotation_line){
                                self.pos.quotation_lines.push(quotation_line[0]);
                            });
                        }
                    });

                    self.gui.close_popup();
                    self.pos.delete_current_order();
                    document.location.reload();
                });
                }
            }
            else {
                if (deliver_date < today){
                    self.gui.show_popup('error',{
                                'title': _t('Please Select Valid Deliver Date!'),
                                'body': _t('Date must be greater than today'),
                            });
                    }
                else{
                    so_val.date_order = order_date;
                    so_val.note = order_note;
                    so_val.phone = phone;
                    so_val.pickup_date = pickup_date;
                    so_val.deliver_date = deliver_date;
                    so_val.delivery_address = delivery_address;
                    so_val.book_order = book_order;
                    rpc.query({
                        model: 'book.order',
                        method: 'create_from_ui',
                        args: [so_val],
                    })
                    .then(function(order){
                        rpc.query({
                            model: 'book.order',
                            method: 'search_read',
                            args: [[['id', '=', order['id']]], fields],
                            limit: 1,
                        })
                        .then(function (quotation){
                            self.pos.quotations.push(quotation[0]);
                             for (var line in quotation[0]['lines']){
                                rpc.query({
                                    model: 'book.order.line',
                                    method: 'search_read',
                                    args: [[['id', '=', quotation[0]['lines'][line]]], line_fields],
                                    limit: 1,
                                }).then(function (quotation_line){
                                self.pos.quotation_lines.push(quotation_line[0]);
                            });
                        }
                    });

                    self.gui.close_popup();
                    self.pos.delete_current_order();
                    document.location.reload();
                    });
                    }
                }
    },

    init: function (parent, options) {
            this._super(parent, options);
    },
     }),

    show: function (options) {
        var self = this;
        this.order_selected = options.order;
        this.client = options.client;
        options = options || {};
        this._super(options);
        this.renderElement();
        var order = self.pos.get_order();
        if (order.attributes.client == null){
              self.gui.show_popup('confirm',{
                                'title': _t('Please select the Customer'),
                                'body': _t('You need to select a customer for using this option'),
                                confirm: function(){
                                    self.gui.show_screen('clientlist');
                                },
                            });
                }

        else if(order.orderlines.length == 0 ){
                self.gui.show_popup('alert', {
                                title: _t('Orderline is empty'),
                                body: _t(
                                  _t('You need to select at least one item'),
                                ),
                            });
                    }
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
    });

gui.define_popup({
        name: 'popup_widget',
        widget: popup_widget
        });

});
