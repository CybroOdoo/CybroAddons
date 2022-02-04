odoo.define('discount_limit.restrict', function (require) {
"use strict";
var models = require('point_of_sale.models');
var core = require('web.core');
var _t = core._t;
const { Gui } = require('point_of_sale.Gui');
const Registries = require('point_of_sale.Registries');
const DiscountButton = require('pos_discount.DiscountButton');
models.load_fields("hr.employee","has_pos_discount_control");

const DiscountLimit = (DiscountButton) =>

    class extends DiscountButton {
        async onClick() {
            var self=this;
        if (this.env.pos.get_cashier().has_pos_discount_control===true){
            Gui.showPopup("ErrorPopup", {
            'title': _t('Discount Restricted'),
             'body': _t('You must be granted access to apply discount '),
            });
        }
        else
        {
          var self = this;
            const { confirmed, payload } = await this.showPopup('NumberPopup',{
                title: this.env._t('Discount Percentage'),
                startingValue: this.env.pos.config.discount_pc,
            });
              if (confirmed) {
                const val = Math.round(Math.max(0,Math.min(100,parseFloat(payload))));
                await self.apply_discount(val);
            }
        }
        }
    }
    Registries.Component.extend(DiscountButton, DiscountLimit);
    return DiscountButton;



});
