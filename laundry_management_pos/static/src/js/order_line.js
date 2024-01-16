odoo.define('laundry_management_pos.orderline', function(require) {
    'use strict';

const Orderline = require('point_of_sale.Orderline');
const Registries = require('point_of_sale.Registries');

var models = require('point_of_sale.models');

//     Extend the order-line used to add popup items
const PosResOrderline = Orderline =>

    class extends Orderline {

       click(){
           this.showPopup("LaundryServiceTypePopup", {
                title : this.env._t("Laundry Service"),
                service: this.env.pos.washing_type,
                pos: this.env.pos,
                orderline: this.props.line,

        });

       }

       //       function to remove the service from the Laundry Process
       remove_laundry(){
            this.props.line.washingType = '';
            this.props.line.washingType_id = 0.0;
            this.props.line.trigger('change',this.props.line);
       }
    };

Registries.Component.extend(Orderline, PosResOrderline);

return Orderline;
});