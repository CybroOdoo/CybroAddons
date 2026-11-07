import { Component, proxy, signal } from "@odoo/owl";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class InventoryReport extends Component {
    setup() {
        super.setup(...arguments);
        this.uiService = useService('ui');
        this.initial_render = true;
        this.orm = useService('orm');
        this.action = useService('action');
        this.start_date = signal.ref();
        this.end_date = signal.ref();
        this.order_by = signal.ref();

        this.state = proxy({
            order_line: [],
            data: null,
            order_by: 'report_by_transfers',
            wizard_id: []
        });
        this.load_data();
    }

    /** Gets values using rpc query */
    async load_data(wizard_id = null) {
        try {
            if (wizard_id == null) {
                this.state.wizard_id = await this.orm.create("dynamic.inventory.report", [{}]);
            }
            this.state.data = await this.orm.call("dynamic.inventory.report", "inventory_report", [this.state.wizard_id]);
            this.state.order_line = this.state.data ? this.state.data.report_lines : [];
        } catch (el) {
            this.state.order_line = [];
        }
    }

    /** Filter applying function */
    async applyFilter(ev) {
        let filter_data = {};
        this.state.order_by = this.order_by().value;
        filter_data.date_from = this.start_date().value;
        filter_data.date_to = this.end_date().value;
        filter_data.report_type = this.order_by().value;
        await this.orm.write("dynamic.inventory.report", this.state.wizard_id, filter_data);
        this.load_data(this.state.wizard_id);
    }

    /** Print pdf report */
    async printPdf(ev) {
        ev.preventDefault();
        return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'all_in_one_inventory_kit.inventory_pdf_report',
            'report_file': 'all_in_one_inventory_kit.inventory_pdf_report',
            'data': {
                'report_data': this.state.data
            },
            'context': {
                'active_model': 'inventory.report',
                'landscape': 1,
                'inventory_pdf_report': true
            },
            'display_name': 'Inventory Report',
        });
    }

    async print_xlsx() {
        /**
         * Generates and downloads an XLSX report for the purchase orders.
         */
        const data = this.state.data;
        const action = {
            'data': {
                'model': 'dynamic.inventory.report',
                'options': JSON.stringify(data ? data['orders'] : {}),
                'output_format': 'xlsx',
                'report_data': JSON.stringify(data ? data['report_lines'] : []),
                'report_name': 'Inventory Report',
                'dfr_data': JSON.stringify(data || {}),
            },
        };
        this.uiService.block();
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } finally {
            this.uiService.unblock();
        }
    }

    /** Click function of order view button */
    button_view_order(ev) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'stock.picking',
            res_id: parseInt(ev.target.id),
            views: [[false, "form"]],
            target: "current",
        });
    }
}

InventoryReport.template = 'all_in_one_inventory_kit.InventoryReport';
registry.category("actions").add("inv_r", InventoryReport);
