/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";

//Extend the props of Orderline to include optional custom functions
Orderline.props = {
    ...Orderline.props,

};
