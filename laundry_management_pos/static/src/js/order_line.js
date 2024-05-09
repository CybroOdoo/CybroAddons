/** @odoo-module */

import { Orderline } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const PosResOrderline = Orderline => class extends Orderline {
    click() {
        this.showPopup("LaundryServiceTypePopup", {
            title: this.env._t("Laundry Service"),
            service: this.env.pos.washing_type,
            pos: this.env.pos,
            orderline: this.props.line,
        });
    }
    remove_laundry() {
    //Method for removing laundry
        this.props.line.washingType = '';
        this.props.line.washingType_id = 0.0;
    }
};
    // Extend Orderline with PosResOrderline
    Registries.Component.extend('Orderline', PosResOrderline);
