/** @odoo-module **/
//Patched order to fetch barcode number and to search for the order related to  barcode
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { rpc } from "@web/core/network/rpc";


patch(PosOrder.prototype, {
     setup() {
        super.setup(...arguments);
        this.barcode_reader = this.barcode_reader || null;
        this.is_barcode = false
        let barcode = _t("%s", this.uid);
        this.barcode = barcode.replace(/-/g, "")
    },
     set_barcode_reader(barcode_reader) {
        this.barcode_reader = barcode_reader.Value;
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
})
