/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ImportRecords } from "@base_import/import_records/import_records";

 patch(ImportRecords.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    },
    async InstantImport() {
        const { context, resModel } = this.env.searchModel;
        this.action.doAction({
            type: "ir.actions.client",
            tag: "instant_import",
            params: { model: resModel, context },
        });
    }
});
