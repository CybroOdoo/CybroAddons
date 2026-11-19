import { patch } from "@web/core/utils/patch";
import { ImportRecords } from "@base_import/import_records/import_records";

patch(ImportRecords.prototype, {
    async InstantImport() {
        const { context, resModel } = this.env.searchModel;
        this.action.doAction({
            type: "ir.actions.client",
            tag: "instant_import",
            path: "instant_import",
            params: { model: resModel, context },
        });
    },
});
