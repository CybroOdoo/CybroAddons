/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Orderline, Order } from "@point_of_sale/app/store/models";

patch(Orderline.prototype, {
    export_as_JSON(){
        var json = super.export_as_JSON.call(this);
        // Check if the product_uom_id is undefined.If yes, set product_uom_id to the default uom_id of the product
        if (this.product_uom_id == undefined){
            this.product_uom_id = this.product.uom_id;
        }
        // Set the product_uom_id in the JSON object
        json.product_uom_id = this.product_uom_id[0];
        return json;
    },
    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        // Set the product_uom_id from the JSON data
        if(this.pos.units_by_id[json.product_uom_id]){
        this.product_uom_id = {
            0 : this.pos.units_by_id[json.product_uom_id].id,
            1 : this.pos.units_by_id[json.product_uom_id].name,
        };
        }
    },
    // Add a custom set_uom method
    set_uom(uom_id){
        this.product_uom_id = uom_id;
    },
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
    },
    onSelectionChangedUom(ev) {
            var splitTargetValue = ev.target.value.split(',')
            var price = splitTargetValue[0]
            var uomId = splitTargetValue[1]
            var uomName = splitTargetValue[2]
            // Set the selected unit of measure on the order line
            const currentOrder = this.env.services.pos.get_order();
            currentOrder.selected_orderline.set_uom({0:uomId,1:uomName})
          // Set the price_manually_set flag to indicate that the price was manually set
            currentOrder.selected_orderline.price_type = "manual";
           // Set the unit price of selected UoM on the order line
            currentOrder.selected_orderline.set_unit_price(price);
    },
     getUom(self) {
        const currentOrder = self.env.services.pos.get_order();
        const currentLine = currentOrder.orderlines.find((line) => line.full_product_name === self.props.line.productName)
        const uom = currentLine.product.pos_multi_uom_ids
        const filteredData = self.env.services.pos.pos_multi_uom.filter(obj => currentLine.product.pos_multi_uom_ids.includes(obj.id));
        return filteredData;
    },
    resetUom(){
        this.select_uom.el.value = 'change_uom';
        const currentOrder = this.env.services.pos.get_order();
        currentOrder.selected_orderline.set_uom({0:currentOrder.selected_orderline.product.uom_id[0],1:currentOrder.selected_orderline.product.uom_id[1]})
        currentOrder.selected_orderline.set_unit_price(currentOrder.selected_orderline.product.lst_price);
    },
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            getUom: this.getUom,
            resetUom: this.resetUom,
            onSelectionChangedUom: this.onSelectionChangedUom,
        };
    },
});
patch(Order.prototype, {
    export_for_printing() {
        var result = super.export_for_printing(...arguments);
        result['orderlines'] =  result['orderlines'].map(({ onSelectionChangedUom, ...rest }) => rest);
        return result;
    },
});