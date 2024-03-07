/** @odoo-module **/

   import { ScaleScreen } from "@point_of_sale/app/screens/scale_screen/scale_screen";
   import { registry } from "@web/core/registry";
   import { patch } from "@web/core/utils/patch";

   patch(ScaleScreen.prototype, {
    async _setWeight() {
        if (!this.shouldRead) {
            return;
        }
        this.state.weight = await Number(document.getElementById("qty_to_add").value)
            setTimeout(() => this._setWeight(), 500);
    }

});