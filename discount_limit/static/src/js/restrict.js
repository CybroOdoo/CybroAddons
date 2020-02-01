odoo.define('discount_limit.restrict', function (require) {
"use strict";

var models = require('point_of_sale.models');
var core = require('web.core');
var pos_screens = require('pos_discount.pos_discount');
var _t = core._t;

models.load_fields("hr.employee","has_pos_discount_control");

pos_screens.DiscountButton.include({
        button_click: function(){
        var self=this;
        if (this.pos.get_cashier().has_pos_discount_control===true){
            this.gui.show_popup('error',{
            'title': _t('Discount Restricted'),
             'body': _t('You must be granted access to apply discount '),
            });
        }
        else
        {  this._super.apply(this);
        }
        },
})
});
