/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { unaccent } from "@web/core/utils/strings";
import { jsonrpc } from "@web/core/network/rpc_service";
import { DebugWidget } from "@point_of_sale/app/debug/debug_widget";
import { useService } from "@web/core/utils/hooks";


patch(DebugWidget.prototype, {
       setup() {
         super.setup()
                 this.orm = useService("orm");
       },
       async barcodeScan() {
            if (!this.barcodeReader) {
                return;
            }
           await this.orm.call('multi.barcode.products','get_barcode_val',[this.state.barcodeInput]).then(async (data) => {
               if (data[1]){
                   this.currentOrder = this.pos.get_order();
                   var product = this.pos.db.get_product_by_id(parseInt(data[1]))
                   this.currentOrder.add_product(product);
               }
               else{
                      await this.barcodeReader.scan(this.state.barcodeInput);
               }
           });
      }
});