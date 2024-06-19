/** @odoo-module */

import { Orderline } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const PosSaleOrderline = (Orderline) => class PosSaleOrderline extends Orderline {
    constructor() {
        super(...arguments);
        this.washingType = this.washingType || arguments[1].washingType;
        this.washingType_id = this.washingType_id || 0.0;
        this.washingType_price = this.washingType_id || 0.0;
    }

    // Function to set the service type of the Washing
    set_washingType(service) {
        this.washingType = service.name;
        this.washingType_id = service.id;
        this.washingType_price = service.amount;
        this.price = service.amount;
    }

    // Function to get the service type of the Washing
    get_washingType() {
        return this.washingType;
    }

    // Used to merge the services with Order-line
    can_be_merged_with(orderline) {
        if (orderline.get_washingType() !== this.get_washingType()) {
            return false;
        } else {
            return super.can_be_merged_with(orderline);
        }
    }

    // Clone the service with order-lines
    clone() {
        var orderline = super.clone();
        orderline.washingType = this.washingType;
        orderline.washingType_id = this.washingType_id;
        orderline.washingType_price = this.washingType_price;
        if(this.washingType_price){
            orderline.price = this.washingType_price;
        }
        return orderline;
    }
    //Add washing type and price to orderline
    export_as_JSON() {
        var json = super.export_as_JSON();
        json.washingType = this.washingType;
        json.washingType_id = this.washingType_id;
        json.washingType_price = this.washingType_price;
        if (this.washingType_price){
            json.price=this.washingType_price;
        }
        return json;
    }
    //Set washing type and price to orderline
    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.washingType = json.washingType;
        this.washingType_id = json.washingType_id;
        this.washingType_price = json.washingType_price;
    }
};
Registries.Model.extend(Orderline, PosSaleOrderline);
export default PosSaleOrderline;
