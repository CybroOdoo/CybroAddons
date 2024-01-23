/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

//Patching the PosStore to load the data from the model hr.employee
patch(PosStore.prototype, {
    //For loading the data from the model hr.employee
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.session_employee = loadedData["hr.employee"];
    }
});
