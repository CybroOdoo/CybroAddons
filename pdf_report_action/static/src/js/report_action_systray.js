import {Component} from '@odoo/owl';
import {registry} from '@web/core/registry';
import {useService} from "@web/core/utils/hooks";

// creating systray menu for report
export class ReportMenu extends Component {
    static template = "pdf_report_action.IconSystrayDropdown";

    setup() {
        this.action = useService("action");
    }
    // Defining a function to open the wizard while clicking the systray menu
    openWizard(ev) {
        if (ev) {
            ev.preventDefault();
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Open Report Wizard",
            res_model: "dynamic.action",
            views: [[false, "form"]],
            target: "new",
        });
    }
}
export const ReportMenuItem = {
    Component: ReportMenu,
};
registry.category("systray").add("pdf_report_action.ReportAction", ReportMenuItem, { sequence: 40 });