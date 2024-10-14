/** @odoo-module **/
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";

export class ExcelListRenderer extends ListRenderer {
    setup() {
    super.setup();
    }
}
//Extends X2ManyField to create widget
export class ExcelX2ManyField extends X2ManyField {
      setup() {
        super.setup()
        this.actionService = useService("action");

      }
     async Print_excel_report(){
        var model = this.props.record.resModel
        var order = this.props.record.resId
        var one2many = this.props.name
        var relation=this.field.relation
        var related_field = this.field.relation_field
        var action = {
                type: "ir.actions.report",
                report_type: "xlsx",
                report_name: 'Excel',
                report_file: "report.excel",
                context:{'model':relation,'id':order,'field':related_field},
        };
        return this.actionService.doAction(action);
    }
}
ExcelX2ManyField.components = {
    ...X2ManyField.components, ListRenderer: ExcelListRenderer
};
ExcelX2ManyField.template = "one2many_excel_report.One2manyExcel";

export const excelX2ManyField = {
    ...x2ManyField,
    component: ExcelX2ManyField,
};

registry.category("fields").add("one2many_excel", excelX2ManyField);
