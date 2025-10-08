/** @odoo-module **/
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
import { patch } from "@web/core/utils/patch";

patch(ExportDataDialog.prototype, 'export_print', {
    setup () {
        this._super()
    },
    async onClickExportButton() {
        this._super()
        // To modify on click function
        let list = {
            records: this.props.root.records.filter(
                element => {
                    return element.selected === true
                }
            ).map(r => {
                return { rec_id: r.resId,
                    rec_model: r.resModel,
                };
            }),
            exportList: this.state.exportList.map(
                r => {
                    return { field_name: r.id,
                    }
                }
            ),
        }
        await this.orm.call(
            "export.log", "action_create_export_log", [0, list]
        )
   }
});
