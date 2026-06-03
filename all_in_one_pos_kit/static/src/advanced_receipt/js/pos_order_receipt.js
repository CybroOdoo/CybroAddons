import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

//Patching PosOrder
patch(PosOrder.prototype, {
    //    supering export_for_printing method to add custom data
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        const partner = this.get_partner();
        if (partner) {
            result.headerData.customer_name = partner.name || false;
            result.headerData.customer_address = partner.contact_address || false;
            result.headerData.customer_mobile = partner.mobile || false;
            result.headerData.customer_phone = partner.phone || false;
            result.headerData.customer_email = partner.email || false;
            result.headerData.customer_vat = partner.vat || false;
        }
        const barcodeValue = this.name || this.pos_reference || "";
        result.headerData.barcode = barcodeValue;
        result.headerData.barcode_url = `/pos/qrcode?value=${encodeURIComponent(barcodeValue)}`;
        console.log('Receipt Header Data:', result.headerData);
        return result;
    },
});