/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { uuidv4} from "@point_of_sale/utils";

patch(PosStore.prototype, {
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.session_orders = loadedData['res.config.settings'];
            var json = {
                access_token: this.access_token || '',
            };
            const options = {pos:this};
            this.pos = options.pos;
            this.access_token = uuidv4();
            const address = `${this.pos.base_url}/pos/ticket/validate?access_token=${this.access_token}`
            var receipt_number = this.selectedOrder
            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
            const qr_code_svg = new XMLSerializer().serializeToString(
                        codeWriter.write(address, 150, 150)
                    );
            this.pos.qr_image = "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
            $(".orderlines").change(function (){
            const address = `${this.base_url}/pos/ticket/validate?access_token=${this.access_token}`
            });
        }
});
