/** @odoo-module **/
/*
 * This file is used to add some fields to order class for some reference.
 */
import Registries from 'point_of_sale.Registries';
import {Order} from 'point_of_sale.models'

const BookedOrder = (Order) => class BookedOrder extends Order {
    constructor(obj, options) {
    // this function is overrided for adding two fields to order and assign value to them
        super(...arguments);
        if (options.json) {
            this.is_booked = options.json.is_booked || false;
            this.booked_data = options.json.booked_data || undefined;
        }
    }
    init_from_JSON(json) {
    // this function is overrided for assigning json value to this
        super.init_from_JSON(...arguments);
        this.is_booked = json.is_booked;
        this.booked_data = json.booked_data
    }
    export_as_JSON() {
    //  this function is overrided for assign this to json for new field
        const json = super.export_as_JSON(...arguments);
        json.booked_data = this.booked_data;
        json.is_booked = this.is_booked;
        return json;
    }
}
Registries.Model.extend(Order, BookedOrder);