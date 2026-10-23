/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

// Safely resolve parent field definition with default fallback null to prevent KeyNotFoundError
const fieldsRegistry = registry.category("fields");
const baseFieldDef =
    fieldsRegistry.get("sol_o2m", null) ||
    fieldsRegistry.get("section_and_note_one2many", null) ||
    x2ManyField;

const BaseComponent = baseFieldDef.component || X2ManyField;

export class ExcelX2ManyField extends BaseComponent {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async printExcelReport() {
        if (this.props.record && this.props.record.isDirty) {
            await this.props.record.save();
        }
        const order = this.props.record ? this.props.record.resId : false;
        const fieldObj =
            this.field ||
            (this.props.record &&
                this.props.record.fields &&
                this.props.record.fields[this.props.name]);
        const relation = fieldObj ? fieldObj.relation : false;
        const relatedField = fieldObj
            ? fieldObj.relation_field || fieldObj.inverse_fname
            : false;
        const action = {
            type: "ir.actions.report",
            report_type: "xlsx",
            report_name: "Excel",
            report_file: "report.excel",
            context: {
                model: relation,
                id: order || false,
                field: relatedField,
            },
        };
        return this.actionService.doAction(action);
    }

    async Print_excel_report() {
        return this.printExcelReport();
    }
}

ExcelX2ManyField.template = "one2many_excel_report.One2manyExcel";

export const excelX2ManyField = {
    ...baseFieldDef,
    component: ExcelX2ManyField,
};

registry.category("fields").add("one2many_excel", excelX2ManyField);



