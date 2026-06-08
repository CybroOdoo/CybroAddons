/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
const actionRegistry = registry.category("actions");
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
    /**
     * CashFlow component displays and manages the cash flow report.
     * It fetches data from the server and renders the report.
     */
class CashFlow extends Component {
    /**
     * Setup method initializes the component.
     * It sets up the ORM service and action service, initializes the state,
     * and fetches the report data.
     */
   setup() {
//   Initialise all variables and services in the setup function
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: [],
            move_lines:[],
            result: []
        });
        this.fetchReportData();
    }
   async fetchReportData() {
    // * Fetches the report data from the server.
        const data = {
            levels: 'detailed',
            target_move: 'posted'
        };
        const result = await this.orm.call("cashflow","get_report_values", [data,data]);
        this.state.result = result
        this.state.data = result.account_res.map(account => {
            return {
                ...account,
                journal_lines: account.journal_lines || [],
                move_lines: account.move_lines || [],
                total_debit: account.journal_lines.reduce((acc, line) => acc + line.total_debit, 0),
                total_credit: account.journal_lines.reduce((acc, line) => acc + line.total_credit, 0),
            };
        });
    }
    gotoJournalEntry(move) {
    //    Navigates to the journal entry form view.
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'account.move',
            res_id: move.move_id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}
CashFlow.components = { Dropdown, DropdownItem}
CashFlow.template = 'CashFlowReportTemplate';
actionRegistry.add("cash_flow_report_tag", CashFlow);
