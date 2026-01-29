odoo.define('laundry_management_pos.LaundryServiceTypePopup', function(require) {
   'use strict';
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const PosComponent = require('point_of_sale.PosComponent');
const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
const NumberBuffer = require('point_of_sale.NumberBuffer');
const { useListener } = require('web.custom_hooks');
const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
const { useState, useRef } = owl.hooks;

class LaundryServiceTypePopup extends AbstractAwaitablePopup {
constructor() {
    super(...arguments);
}

//  Create a new Popup instance
laundryPopup(event){
        var order = this.props.pos.get_order();
        if (!this.props.orderline) {
              order.selected_orderline.set_washingType(event.currentTarget.dataset);
        }
        else{
            this.props.orderline.set_washingType(event.currentTarget.dataset);
            this.props.orderline.trigger('change',this.props.orderline);
        }
        this.trigger('close-popup');
    }

}
//Create Service popup
LaundryServiceTypePopup.template = 'LaundryServiceTypePopup';
LaundryServiceTypePopup.defaultProps = {
   confirmText: 'Ok',
   cancelText: 'Cancel',
};
Registries.Component.add(LaundryServiceTypePopup);

return LaundryServiceTypePopup;
});
