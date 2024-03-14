/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
/** Patch ProductScreen for override the getNumpadButtons function  **/
patch(ProductScreen.prototype,{
    setup(){
        super.setup()
        this.env.services.pos.user_session = [];
        this.env.services.pos.button = [];

        onWillStart(async () => {
            var session;
                if (this.env.services.pos.res_user.length !== 0) {
                    session = this.env.services.pos.res_user.user_session_ids;
                } else {
                    session = false;
                }
                var hide_buttons;
                if (this.env.services.pos.res_user.length !== 0) {
                    hide_buttons = this.env.services.pos.res_user.buttons_pos_ids;
                } else {
                    hide_buttons = false;
                }
                this.def = await this.env.services.orm.call("res.users", "pos_button_visibility", [,hide_buttons]);
                this.env.services.pos.user_session = session;
        })
    },
    getNumpadButtons() {
        return [
            { value: "1" },
            { value: "2" },
            { value: "3" },
            { value: "quantity", text: "Qty" },
            { value: "4" },
            { value: "5" },
            { value: "6" },
            { value: "discount", text: "% Disc", disabled: !this.pos.config.manual_discount || this.def.includes('Discount') },
            { value: "7" },
            { value: "8" },
            { value: "9" },
            { value: "price", text: "Price", disabled: !this.pos.cashierHasPriceControlRights() ||this.def.includes('Price') },
            { value: "-", text: "+/-" },
            { value: "0" },
            { value: this.env.services.localization.decimalPoint },
            // Unicode: https://www.compart.com/en/unicode/U+232B
            { value: "Backspace", text: "⌫" },
        ].map((button) => ({
            ...button,
            class: this.pos.numpadMode === button.value ? "active border-primary" : "",
        }));
    }
});
