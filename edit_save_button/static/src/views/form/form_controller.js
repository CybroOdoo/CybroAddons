/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController, "form_controller", {
    defaultProps: {
        ...FormController.defaultProps,
        preventEdit: true,
    }
});

patch(FormController.prototype, "save",{
    async saveButtonClicked(params = {}){
        this._super();
        await this.model.root.switchMode("readonly");
    },
    async discard(){
        this._super();
        await this.model.root.switchMode("readonly");
    }
})








