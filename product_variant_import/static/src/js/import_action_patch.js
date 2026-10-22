/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ImportAction } from "@base_import/import_action/import_action";

patch(ImportAction.prototype, {
    async onWillStart() {
        await super.onWillStart(...arguments);
        const importId = this.props.action.params?.import_id;
        if (importId) {
            this.model.id = importId;
            const fileName = this.props.action.params?.file_name || "imported_file.xlsx";
            this.state.filename = fileName;
            this.env.config.setDisplayName(`Import ${fileName}`);
            this.model.block("Loading file...");
            const { res, error } = await this.model.updateData(true);
            if (error) {
                this.state.previewError = error;
            } else {
                this.state.numRows = res.num_rows;
                this.state.previewError = undefined;
            }
            this.model.unblock();
        }
    }
});
