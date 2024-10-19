/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
const actionRegistry = registry.category("actions");
import { uiService } from "@web/core/ui/ui_service";
//  Extending components for adding purchase report class
class SaleReport extends Component {
    async setup() {
        super.setup(...arguments);
        this.uiService = useService('ui');
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.start_date = useRef('date_from');
        this.end_date = useRef('date_to');
        this.order_by = useRef('order_by');
        this.state = useState({
            order_line: [],
            data: null,
            order:'Report By Sale Order',
            order_by : 'report_by_order',
            wizard_id : []
        });
        this.load_data();
        }
    async load_data(wizard_id = null) {
        /**
         * Loads the data for the sales report.
         */
        let move_lines = ''
        try {
            if(wizard_id == null){
                this.state.wizard_id = await this.orm.create("sales.report",[{}]);
                }
            this.state.data = await this.orm.call("sales.report", "sale_report", [this.state.wizard_id]);
            this.state.order_line = this.state.data.report_lines
        }
        catch (el) {
            window.location.href
        }
    }
    async apply_filter(ev) {
        let filter_data = {}
        this.state.order_by = this.order_by.el.value
        this.state.order = this.order_by.el.selectedOptions[0].outerText
        filter_data.date_from = this.start_date.el.value
        filter_data.date_to = this.end_date.el.value
        filter_data.report_type = this.order_by.el.value
        let data = await this.orm.write("sales.report",this.state.wizard_id, filter_data);
        this.load_data(this.state.wizard_id)
    }
    //This function call an rpc call to the model sales.report & function sale_report with args wizard_id
    async PrintPdf(ev){
        /**
         * Generates and displays a PDF report for the sale orders.
         *
         * @param {Event} ev - The event object triggered by the action.
         * @returns {Promise} - A promise that resolves to the result of the action.
         */
        ev.preventDefault();
        var self = this;
        var action_title = self.props.action.display_name;
        return self.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'sale_report_generator.sale_order_report',
            'report_file': 'sale_report_generator.sale_order_report',
            'data': {
                'report_data': this.state.data
            },
            'context': {
						'active_model': 'sales.report',
						'landscape': 1,
						'sale_order_report': true
					},
			'display_name': 'sale Order',
        });
    }
    async PrintXlsx(){
        /**
         * Generates and downloads an XLSX report for the sale orders.
         */
        var data = this.state.data
        var action = {
					'data': {
						'model': 'sales.report',
						'options': JSON.stringify(data['orders']),
						'output_format': 'xlsx',
						'report_data': JSON.stringify(data['report_lines']),
						'report_name': 'Sales Report',
						'dfr_data': JSON.stringify(data),
					},
				};
        this.uiService.block();
        await download({
            url: '/sale_dynamic_xlsx_reports',
            data: action.data,
            complete: this.uiService.unblock(),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
          });
    }
    //Corresponding SaleOrder Tree,Form View
    async viewSaleOrder(ev){
    return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'sale.order',
            res_id: parseInt(ev.target.id),
            views: [[false, "form"]],
            target: "current",
        });
    }
}
SaleReport.template = 'SaleReport';
actionRegistry.add("sales_report", SaleReport);
