odoo.define('laundry_management_pos.LaundryServiceType', function (require) {
 "use strict";
const { Gui } = require('point_of_sale.Gui');
const { useListener } = require('web.custom_hooks');
const PosComponent  = require('point_of_sale.PosComponent');
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const ProductItem = require('point_of_sale.ProductItem');
const ProductScreen = require('point_of_sale.ProductScreen');
var models = require('point_of_sale.models');
var rpc = require('web.rpc');

models.load_models({
model:  'washing.type',
fields: ['name','assigned_person', 'amount'],
loaded: function(self, washing_type) {
        self.washing_type = washing_type;
    }
})

class LaundryServiceButton extends PosComponent{
   constructor() {
        super(...arguments);
        useListener('click', this.onClick);
    }

  //Generate popup
   async onClick() {
      var core = require('web.core');
      var _t = core._t;
      this.showPopup("LaundryServiceTypePopup", {
           title : _t("Laundry Service"),
           confirmText: _t("Exit"),
           service: this.env.pos.washing_type,
           pos: this.env.pos,
      });
  }
}

LaundryServiceButton.template = 'LaundryServiceButton';

//Add popup button and set visibility
  ProductScreen.addControlButton({
  component: LaundryServiceButton,
  condition: function() {
      return this.env.pos.config.orderline_washing_type;
  },
});
Registries.Component.add(LaundryServiceButton);

return LaundryServiceButton;
});
