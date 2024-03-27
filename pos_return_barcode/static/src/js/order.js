/** @odoo-module **/
//Patched order to fetch barcode number and to search for the order related to  barcode
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
     setup(_defaultObj, options) {
        super.setup(...arguments);
        this.barcode_reader = this.barcode_reader || null;
        this.orm = options.pos.orm;
        this.is_barcode = false
        this.barcode = null
        },

     set_barcode_reader(barcode_reader) {
        this.comment_feedback = barcode_reader.Value;
    },
    get_barcode_reader() {
        return this.barcode_reader;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.barcode_reader = this.barcode_reader;
        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.barcode_reader = json.barcode_reader;
    },
     async get_barcode(){
     this.is_barcode = await this.orm.call("ir.config_parameter", "get_param", ["pos_return_barcode.receipt_barcode"])
     const order = await this.orm.searchRead("pos.order",
                   [["id", "=", this.server_id]],
                   ['barcode']);
     if(this.is_barcode){
     order.forEach(element =>{
        this.barcode = element.barcode
        })
        }
        return this.barcode
     },
   export_for_printing() {
   this.get_barcode()
        return {
            ...super.export_for_printing(...arguments),
            is_barcode: this.is_barcode,
            barcode: this.barcode,
          };
          },
})
