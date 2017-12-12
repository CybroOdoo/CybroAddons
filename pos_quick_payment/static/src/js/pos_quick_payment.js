odoo.define('pos_quick_payment.quick_payment', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var core = require('web.core');
var Model = require('web.DataModel');
var utils = require('web.utils');
var formats = require('web.formats');

var screens = require('point_of_sale.screens');
var PaymentScreenWidget = screens.PaymentScreenWidget;

var QWeb = core.qweb;
var _t = core._t;

var round_pr = utils.round_precision;

models.load_models({
    model: 'pos.quick.payment',
        fields: ['name'],
        domain: function(self){ return [['id','in',self.config.payment_options]];},
        loaded: function(self, quick_payments){
            self.quick_payments = quick_payments;
        },
    });

PaymentScreenWidget.include({
    renderElement: function() {
        this._super();
        if (this.pos.config.quick_payment){
            var quick_payment = this.render_quick_payment();
            quick_payment.appendTo(this.$('.quick_payment-container'));
        }


    },

    render_quick_payment: function() {
        var self = this;
        var quick_payment = $(QWeb.render('PaymentScreen-QuickPayment', { widget:this }));
        quick_payment.on('click','.quick_payment',function(){
            self.click_quick_payment($(this).data('value'));
        });
        return quick_payment;
    },

    click_quick_payment: function(value){
        var self = this;
        var paymentlines = this.pos.get_order().get_paymentlines();
	    var open_paymentline = false;
	    var payment_line = null;
        var cashregister = null;
        if(! self.pos.config.quick_payment_journal){
            self.gui.show_popup('alert',{
                'title': 'No journal configured',
                'body':  'Please configure journal for quick payment.',
            });
        }
        else{
        for (var i = 0; i < paymentlines.length; i++) {
            if (paymentlines[i].cashregister.journal_id[0] === self.pos.config.quick_payment_journal[0]) {
            open_paymentline = true;
            payment_line = paymentlines[i];
            break;
            }
        }
        if (! open_paymentline){
            for ( var i = 0; i < self.pos.cashregisters.length; i++ ) {
                if ( self.pos.cashregisters[i].journal_id[0] === self.pos.config.quick_payment_journal[0]){
                    cashregister = self.pos.cashregisters[i];
                    break;
                }
            }
            this.pos.get_order().add_paymentline(cashregister);
            this.reset_input();
            this.render_paymentlines();
            this.payment_input(value);
        }
        else{
            this.pos.get_order().select_paymentline(payment_line);
            this.reset_input();
            this.render_paymentlines();
            this.payment_input(payment_line.amount+value);
        }
        }
    }
});

});