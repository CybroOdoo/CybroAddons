/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { archParseBoolean } from "@web/views/utils";
import { STATIC_ACTIONS_GROUP_NUMBER } from "@web/search/action_menus/action_menus";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
import { ExportDialog } from "../js/export_dialog";
import { Component } from "@odoo/owl";

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
        var self = this.__owl__.parent.parent.parent.parent.parent.component;
        const fields = this.__owl__.parent.parent.parent.parent.parent.component.props.archInfo.columns
            .filter((col) => col.type === "field")
            .map((col) => this.__owl__.parent.parent.parent.parent.parent.component.props.fields[col.name])
        const exportField = [];
        const exportedFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
        }));
        const resIds = await this.__owl__.parent.parent.parent.parent.parent.component.getSelectedResIds();
        this.__owl__.parent.parent.parent.parent.parent.component.dialogService.add(ExportDialog, {
                title: _t("Export PDF"),
                context: exportedFields,
                confirm: () => {
                    let checkboxes = document.querySelectorAll(`#${'check'} input[type="checkbox"]`);
                    checkboxes.forEach(item => {
                        if (item.checked === true){
                            exportField.push({name:item.name,label:item.value})
                        }
                    });
                    var length_field = Array.from(Array(exportField.length).keys());
                    jsonrpc('/get_data',{
                        'model':this.__owl__.parent.parent.parent.parent.parent.component.model.root.resModel,
                        'res_ids':resIds.length > 0 && resIds,
                        'fields':exportField,
                        'grouped_by':this.__owl__.parent.parent.parent.parent.parent.component.model.root.groupBy,
                        'context': this.__owl__.parent.parent.parent.parent.parent.component.props.context,
                        'domain':this.__owl__.parent.parent.parent.parent.parent.component.model.root.domain,
                        'context':this.__owl__.parent.parent.parent.parent.parent.component.props.context,
                    }).then( function (data){
                        if (self.model.root.groupBy[0]){
                            var group_length=Array.from(Array(self.model.root.groups));
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
                        return self.model.action.doAction(action);
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
        await env.model.user.hasGroup("base.group_allow_export") &&
        archParseBoolean(env.config.viewArch.getAttribute("export_xlsx"), true),
};
cogMenuRegistry.add("export-pdf-menu", exportPdfItem, { sequence: 10 });
