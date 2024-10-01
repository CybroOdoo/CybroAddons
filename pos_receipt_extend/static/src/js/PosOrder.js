import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

//Patching PosOrder
patch(PosOrder.prototype, {
//    supering export_for_printing method to add custom data
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        if (this.partner_id){
            result.headerData.customer_name = this.partner_id.name;
            result.headerData.customer_address = this.partner_id.contact_address;
            result.headerData.customer_mobile = this.partner_id.mobile;
            result.headerData.customer_phone = this.partner_id.phone;
            result.headerData.customer_email = this.partner_id.email;
            result.headerData.customer_vat = this.partner_id.vat;
        }
        return result;
    },
});