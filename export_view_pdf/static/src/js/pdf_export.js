/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { exprToBoolean } from "@web/core/utils/strings";
import { STATIC_ACTIONS_GROUP_NUMBER } from "@web/search/action_menus/action_menus";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { ExportDialog } from "./export_dialog";
import { Component } from "@odoo/owl";
import { user } from "@web/core/user";
const cogMenuRegistry = registry.category("cogMenu");
/**
 * 'Export PDF' menu
 *
 * This component is used to export PDF the records for particular model.
 * @extends Component
 */
export class ExportPdf extends Component {
    static template = "web.ExportPdf";
    static components = { DropdownItem };
    //---------------------------------------------------------------------
    // Protected
    //---------------------------------------------------------------------
//  method to define the functionality when clicking on the export pdf menu
    async onDirectExportPdf() {
        this.env.searchModel.trigger('direct-export-pdf');
        const exportField = [];
        const exportedFields = Object.values(this.env.model.config.fields).map(field => ({
            name: field.name,  // Assuming `field` has a `name` property
            label: field.label || field.string,  // Use field properties like label or string
        }));
        const resIds = await this.env.model.root.getResIds();
        this.env.model.dialog.add(ExportDialog, {
                title: _t("Export PDF"),
                context: exportedFields,
                confirm: async () => {
                    let checkboxes = document.querySelectorAll(`#${'check'} input[type="checkbox"]`);
                    checkboxes.forEach(item => {
                        if (item.checked === true){
                            exportField.push({name:item.name,label:item.value})
                        }
                    });
                    var length_field = Array.from(Array(exportField.length).keys());
                    await rpc('/get_data',{
                        'model':this.env.model.config.resModel,
                        'res_ids':resIds.length > 0 && resIds,
                        'fields':exportField,
                        'grouped_by':this.env.model.config.groupBy,
                        'context': this.env.model.config.context,
                        'domain':this.env.model.config.domain,
                    }).then(data => {
                        if (this.env.model.config.groupBy[0]){
                            var action = {
                                'type': 'ir.actions.report',
                                'report_type': 'qweb-pdf',
                                'report_name':'export_view_pdf.export_in_pdf_group_by',
                                'data':{'length':length_field,'group_len':[0,1,2,3],'record':data,}
                            };
                        }
                        else{
                            var action = {
                                'type': 'ir.actions.report',
                                'report_type': 'qweb-pdf',
                                'report_name':'export_view_pdf.export_in_pdf',
                                'data':{'length':length_field,'record':data}
                            };
                        }
                        return this.env.model.action.doAction(action);
                    });
                },
                cancel: () => {},
            });
    }
}
// for adding export pdf menu item
export const exportPdfItem = {
    Component: ExportPdf,
    groupNumber: STATIC_ACTIONS_GROUP_NUMBER,
    isDisplayed: async (env) =>
        env.config.viewType === "list" &&
        !env.model.root.selection.length &&
        await user.hasGroup("base.group_allow_export") &&
        exprToBoolean(env.config.viewArch.getAttribute("export_xlsx"), true),
};
cogMenuRegistry.add("export-pdf-menu", exportPdfItem, { sequence: 10 });
