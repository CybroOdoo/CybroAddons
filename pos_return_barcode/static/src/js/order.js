/** @odoo-module **/
import { Order } from 'point_of_sale.models';
import models from 'point_of_sale.models';
import  Registries from "point_of_sale.Registries";
var rpc = require('web.rpc');
var { Orderline} = require('point_of_sale.models');

const PosReturnOrder = (Order) => class PosReturnOrder extends Order {
    constructor() {
        super(...arguments);
        this.barcode_reader = this.barcode_reader || null;
        this.is_barcode = false
        this.barcode = false
    }
    set_barcode_reader(barcode_reader) {
        this.comment_feedback = barcode_reader.Value;
    }
    get_barcode_reader() {
        return this.barcode_reader;
    }
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.barcode_reader = this.barcode_reader;
        return json;
    }
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.barcode_reader = json.barcode_reader;
    }
    async get_barcode(){
         this.is_barcode = await rpc.query({
            model: "ir.config_parameter",
            method: 'get_param',
            args: ['pos_return_barcode.receipt_barcode'],
         })
         const order = await rpc.query({
            model: 'pos.order',
            method: 'search_read',
            domain: [['pos_reference', '=', this.name]],
            fields:['name','barcode']
         });
        if(this.is_barcode){
            order.map(element => this.barcode = element.barcode)
        }
        return this.barcode
    }
     export_for_printing() {
        this.get_barcode()
        return {
            ...super.export_for_printing(...arguments),
            is_barcode: this.is_barcode,
            barcode: this.barcode,
        };
     }
}
Registries.Model.extend(Order, PosReturnOrder);

