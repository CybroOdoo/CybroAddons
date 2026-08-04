/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
const actionRegistry = registry.category("actions");
import { uiService } from "@web/core/ui/ui_service";
// Extending components for adding purchase report class
class PurchaseReport extends Component {
    async setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
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
            order_by : 'report_by_order',
            wizard_id : []
        });
        this.reportTypeLabels = {
            report_by_order: 'Report By Order',
            report_by_order_detail: 'Report By Order Detail',
            report_by_product: 'Report By Product',
            report_by_categories: 'Report By Categories',
            report_by_purchase_representative: 'Report By Purchase Representative',
            report_by_state: 'Report By State',
        };
        this.load_data();
    }
    get reportLabel() {
        return this.reportTypeLabels[this.state.order_by] || this.state.order_by;
    }
    async load_data(wizard_id = null) {
        /**
        * Loads the data for the purchase report.
        */
        let move_lines = ''
        try {
            if(wizard_id == null){
                this.state.wizard_id = await this.orm.create("dynamic.purchase.report",[{}]);
            }
            this.state.data = await this.orm.call("dynamic.purchase.report", "purchase_report", [this.state.wizard_id]);
            if (Array.isArray(this.state.data)) {
                this.state.order_line = this.state.data.map(item => {
                    return item;
                });
            } else if (typeof this.state.data === 'object' && this.state.data !== null) {
                this.state.order_line = this.state.data.report_lines;
            }
        }
        catch (el) {
            window.location.href;
        }
    }
    async onchangeFromDate() {
        // Validation for start date
        if (this.end_date.el.value && this.start_date.el.value > this.end_date.el.value) {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'End date should be greater than the start date.',
                    type: 'warning',
                    sticky: false,
                }
            });
            this.start_date.el.value = ''
            this.end_date.el.value = ''
        }
    }
    async onchangeEndDate() {
        // Validation for end date
        if (this.start_date.el.value && this.start_date.el.value > this.end_date.el.value) {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'End date should be greater than the start date.',
                    type: 'warning',
                    sticky: false,
                }
            });
            this.start_date.el.value = ''
            this.end_date.el.value = ''
        }
    }
    async applyFilter(ev) {
        let filter_data = {}
        this.state.order_by = this.order_by.el.value
        filter_data.date_from = this.start_date.el.value
        filter_data.date_to = this.end_date.el.value
        filter_data.report_type = this.order_by.el.value
        let data = await this.orm.write("dynamic.purchase.report",this.state.wizard_id, filter_data);
        this.load_data(this.state.wizard_id)
    }
    viewPurchaseOrder(ev) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'purchase.order',
            res_id: parseInt(ev.target.id),
            views: [[false, "form"]],
            target: "current",
        });
    }
    async print_xlsx() {
        /**
        * Generates and downloads an XLSX report for the purchase orders.
        */
        var data = this.state.data
        if (data.report_lines && data.report_lines.length > 0) {
            const action = {
                'data': {
                    'model': 'dynamic.purchase.report',
                    'options': JSON.stringify(data['orders']),
                    'output_format': 'xlsx',
                    'report_data': JSON.stringify(data['report_lines']),
                    'report_name': 'Purchase Report',
                    'dfr_data': JSON.stringify(data),
                },
            };
            this.uiService.block();
            await download({
                url: '/purchase_dynamic_xlsx_reports',
                data: action.data,
                complete: this.uiService.unblock(),
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
        } else {
            // Notify the user if there's no data
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'No data available to print',
                    type: 'warning',
                    sticky: false,
                }
            });
        }
    }
    async printPdf(ev) {
        /**
        * Generates and displays a PDF report for the purchase orders.
        *
        * @param {Event} ev - The event object triggered by the action.
        * @returns {Promise} - A promise that resolves to the result of the action.
        */
        ev.preventDefault();
        var self = this;
        var action_title = self.props.action.display_name;
        var data = this.state.data
        if (data.report_lines && data.report_lines.length > 0) {
            return self.action.doAction({
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': 'purchase_report_generator.purchase_order_report',
                'report_file': 'purchase_report_generator.purchase_order_report',
                'data': {
                    'report_data': data
                },
                'context': {
                    'active_model': 'purchase.report',
                    'purchase_order_report': true
                },
                'display_name': 'Purchase Order',
            })
        } else {
            // Notify the user if there's no data
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'No data available to print',
                    type: 'warning',
                    sticky: false,
                }
            });
        }
    }
}
PurchaseReport.template = 'PurchaseReport';
actionRegistry.add("purchase_report", PurchaseReport);
