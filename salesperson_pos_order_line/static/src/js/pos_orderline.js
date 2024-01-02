/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";

//Patching Orderline to change the uom by adding a function.
patch(Orderline.prototype, {
        setup(_defaultObj, options) {
        super.setup(...arguments);
        if(options.json){
        this.salesperson = this.salesperson;
        this.user_id = this.user_id;
        }
    },
    export_as_JSON(){
        var json = super.export_as_JSON.call(this);
        json.salesperson = this.salesperson || false
        json.user_id = this.user_id || false
            return json
    },
            // Set the unit from the JSON data
    init_from_JSON(json){
        super.init_from_JSON(...arguments);
         this.salesperson = json.salesperson;
         this.user_id = json.user_id;
    },
    get_salesperson(){
    return this.sales_person , this.user_id },
     getDisplayData() {
        return {
            ...super.getDisplayData(),
            salesperson: this.salesperson,
            user_id: this.user_id,
        };
    },
});
