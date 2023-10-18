/** @odoo-module **/

// Import the required modules
import Registries from 'point_of_sale.Registries';
import {Orderline} from 'point_of_sale.models';

// Extend the Orderline class
const ProductUom = (Orderline) => class ProductUom extends Orderline {
    export_as_JSON(){
        var json = super.export_as_JSON.call(this);
        // Check if the product_uom_id is undefined.If yes, set product_uom_id to the default uom_id of the product
        if (this.product_uom_id == undefined){
            this.product_uom_id = this.product.uom_id;
        }
        // Set the product_uom_id in the JSON object
        json.product_uom_id = this.product_uom_id[0];
        return json;
    }
    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        // Set the product_uom_id from the JSON data
        this.product_uom_id = {
            0 : this.pos.units_by_id[json.product_uom_id].id,
            1 : this.pos.units_by_id[json.product_uom_id].name,
        };
    }
    // Add a custom set_uom method
    set_uom(uom_id){
        this.product_uom_id = uom_id;
    }

    // Override the get_unit method to get selected UoM from POS
    get_unit() {
    if (this.product_uom_id){
        var unit_id = this.product_uom_id[0];
        if(!unit_id){
            return undefined;
        }
        if(!this.pos){
            return undefined;
        }
        return this.pos.units_by_id[unit_id];
    }
    return this.product.get_unit();
	}
}
Registries.Model.extend(Orderline, ProductUom);
