/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;

ListController.prototype.actionDef = async function(){
    var self=this;
    const fields = this.props.archInfo.columns
        .filter((col) => col.type === "field")
        .map((col) => this.props.fields[col.name])
    const exportField = [];
    const exportedFields = fields.map((field) => ({
        name: field.name,
        label: field.label || field.string,
    }));
    const resIds = await this.getSelectedResIds();
    const execute = () => {
        let checkboxes = document.querySelectorAll(`#${'check'} input[type="checkbox"]`);
        checkboxes.forEach(item => {
        if (item.checked === true){
            exportField.push({name:item.name,label:item.value})
            }
        });
        var length_field = Array.from(Array(exportField.length).keys());
        ajax.jsonRpc('/get_data','call',{
        'model':this.model.root.resModel,
        'res_ids':resIds.length > 0 && resIds,
        'fields':exportField,
        'grouped_by':this.model.root.groupBy,
        'context': this.props.context,
        'domain':this.model.root.domain,
        'context':this.props.context,
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
    };
    new Dialog(this,{
        title: "Export PDF ",
        $content :  $(QWeb.render('ExportPdf.List', {
            examples: exportedFields,
        })),
        size: 'large',
        buttons: [
                    {
                        text: _t("Export"), classes: 'btn-primary', close: true,
                        click: execute
                    },
                    {
                        text: _t("Cancel"), close: true
                    },
                ],
    }).open();
}
