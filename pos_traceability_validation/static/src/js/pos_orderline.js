/** @odoo-module */
import { Orderline } from "@point_of_sale/app/store/models"
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { CustomButtonPopup } from "./CustomPopup";

patch(Orderline.prototype,  {

    async set_quantity(quantity, keep_price) {
//      Checking the orderline quantity and onhand lot quantity
        super.set_quantity(quantity, keep_price);
        var lines = await this.get_lot_lines()
        if(lines.length){
            var product_id = this.get_product().id
            var lot_name = lines[0].lot_name
            const result = await this.pos.orm.call(
                "stock.lot", "get_available_lots_qty_pos", [product_id, lot_name], {}
            )
            if (quantity > result) {
                this.quantity = result
                await this.env.services.popup.add(CustomButtonPopup, {
                   title: _t("Exception"),
               });
                browser.location.reload()
            }
        }
    }
});
