import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { Component, proxy, signal } from "@odoo/owl";

const actionRegistry = registry.category("actions");

class PurchaseReport extends Component {
    startDate = signal.ref();
    endDate = signal.ref();
    orderBy = signal.ref();

    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.uiService = useService('ui');
        this.orm = useService('orm');
        this.state = proxy({
            order_line: [],
            data: null,
            order_by: 'report_by_order',
            wizard_id: []
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
        try {
            if (wizard_id == null) {
                this.state.wizard_id = await this.orm.create("dynamic.purchase.report", [{}]);
            }
            this.state.data = await this.orm.call(
                "dynamic.purchase.report",
                "purchase_report",
                [this.state.wizard_id]
            );
            if (Array.isArray(this.state.data)) {
                this.state.order_line = this.state.data.map(item => item);
            } else if (typeof this.state.data === 'object' && this.state.data !== null) {
                this.state.order_line = this.state.data.report_lines || [];
            }
        } catch (_e) {
            // Handled silently
        }
    }

    async onchangeFromDate() {
        // Validation for start date
        if (this.endDate().value && this.startDate().value > this.endDate().value) {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'End date should be greater than the start date.',
                    type: 'warning',
                    sticky: false,
                }
            });
            this.startDate().value = '';
            this.endDate().value = '';
        }
    }

    async onchangeEndDate() {
        // Validation for end date
        if (this.startDate().value && this.startDate().value > this.endDate().value) {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'End date should be greater than the start date.',
                    type: 'warning',
                    sticky: false,
                }
            });
            this.startDate().value = '';
            this.endDate().value = '';
        }
    }

    async applyFilter(_ev) {
        this.state.order_by = this.orderBy().value;
        const filter_data = {
            date_from: this.startDate().value,
            date_to: this.endDate().value,
            report_type: this.orderBy().value,
        };
        await this.orm.write("dynamic.purchase.report", this.state.wizard_id, filter_data);
        this.load_data(this.state.wizard_id);
    }

    viewPurchaseOrder(ev) {
        ev.preventDefault();
        return this.actionService.doAction({
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
        const data = this.state.data;
        if (data && data.report_lines && data.report_lines.length > 0) {
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
                complete: () => this.uiService.unblock(),
                error: (error) => this.actionService.doAction({
                    type: 'ir.actions.client',
                    tag: 'display_notification',
                    params: {
                        message: String(error),
                        type: 'danger',
                        sticky: false,
                    }
                }),
            });
        } else {
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
         */
        ev.preventDefault();
        const data = this.state.data;
        if (data && data.report_lines && data.report_lines.length > 0) {
            return this.actionService.doAction({
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': 'purchase_report_generator.purchase_order_report',
                'data': {
                    'report_data': data
                },
                'context': {
                    'active_model': 'purchase.report',
                    'purchase_order_report': true
                },
                'display_name': 'Purchase Order',
            });
        } else {
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
