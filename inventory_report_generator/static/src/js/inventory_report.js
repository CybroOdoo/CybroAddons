/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component,useRef, onMounted} = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

export class InventoryReport extends Component {
    /**
     * Initializes the InventoryReport component.
     */
    setup() {
        this.action = useService("action");
        self.initial_render = false;
        this.table_view_pr = useRef('table_view_pr');
        this.date_from = useRef('date_from');
        this.date_to = useRef('date_to');
        this.report_type = useRef('report_type');
        this.report_res = useRef('report_res');
        this.dates = useRef('dates');
        onMounted(async () => {
        var self = this;
        self.initial_render = true;
        await rpc('/web/dataset/call_kw/dynamic.inventory.report/create', {
            model: 'dynamic.inventory.report',
            method: 'create',
            args: [{}],
            kwargs: {},
        }).then(async function(res) {
            self.wizard_id = res;
            await self.load_data(self.initial_render);
            self.apply_filter();
        })
        });
    }
    /**
     * Loads data for the report.
     *
     * @param {boolean} initial_render - Indicates if it's the initial render.
     */
    async load_data(initial_render = true) {
        var self = this;
        await rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
            model: 'dynamic.inventory.report',
            method: 'inventory_report',
            args: [
                [this.wizard_id]
            ],
            kwargs: {},
        }).then(function(datas) {
            if (datas['orders'] ) {
                self.table_view_pr.el.innerHTML = '';
                self.table_view_pr.el.append(renderToElement('InventoryReportTable', {
                    filter: datas['filters'],
                    order: datas['orders'],
                    report_lines: datas['report_lines'],
                    main_lines: datas['report_main_line'],
                    this: self,
                }))
            }
        })
    }
    /**
     * Applies filters to the report.
     */
    apply_filter() {
        var self = this;
        self.initial_render = false;
        var filter_data_selected = {};

        function setFilterValue(selector, key, target) {
            var value =selector.el.value;
            if (value) {
                filter_data_selected[key] = value;
                target.el.innerHTML = value;
            }
        }
        setFilterValue(self.date_from, 'date_from', this.dates);
        setFilterValue(self.date_to, 'date_to', this.dates);
        if (filter_data_selected.date_from && filter_data_selected.date_to) {
            self.dates.el.innerHTML = filter_data_selected.date_from + " to " + filter_data_selected.date_to;
        }
        if (self.report_type) {
            var report_res = self.report_res;
            filter_data_selected.report_type = self.report_type.el.value;
            report_res.el.innerHTML = self.report_type.el.options[self.report_type.el.selectedIndex].text || "report_by_order";
        }
        rpc('/web/dataset/call_kw/dynamic.inventory.report/write', {
            model: 'dynamic.inventory.report',
            method: 'write',
            args: [self.wizard_id, filter_data_selected],
            kwargs: {},
        }).then(function(res) {
            self.initial_render = false;
            self.load_data(self.initial_render);
        });
    }
    /**
     * Prints the report as a PDF.
     *
     * @param {Event} e - The event object.
     */
    print_pdf(e) {
        e.preventDefault();
        var self = this;
        var action_title = self._title;
        rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
            model: 'dynamic.inventory.report',
            method: 'inventory_report',
            args: [
                [self.wizard_id]
            ],
            kwargs: {},
        }).then(function(data) {
            var action = {
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': 'inventory_report_generator.inventory_pdf_report',
                'report_file': 'inventory_report_generator.inventory_pdf_report',
                'data': {
                    'report_data': data
                },
                'context': {
                    'active_model': 'inventory.report',
                    'landscape': 1,
                    'inventory_pdf_report': true
                },
                'display_name': 'Inventory Report',
            };
            return self.action.doAction(action);
        });
    }
    /**
     * Opens a view for a specific order.
     *
     * @param {Event} ev - The event object.
     */
    button_view_order(ev) {
        ev.preventDefault();
        var self = this;
        var context = {};
        this.action.doAction({
            name: _t("Transfer Order"),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_type: 'form',
            domain: [
                ['id', '=', ev.target.id]
            ],
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        });
    }
    /**
     * Exports the report data as an XLSX file.
     */
    print_xlsx() {
        var self = this;
        rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
            model: 'dynamic.inventory.report',
            method: 'inventory_report',
            args: [
                [self.wizard_id]
            ],
            kwargs: {},
        }).then(function(data) {
            var action = {
                'data': {
                    'model': 'dynamic.inventory.report',
                    'options': JSON.stringify(data['orders']),
                    'output_format': 'xlsx',
                    'report_data': JSON.stringify(data['report_lines']),
                    'report_name': 'Inventory Report',
                    'dfr_data': JSON.stringify(data),
                },
            };
            self.downloadXlsx(action);
        });
    }
    /**
     * Downloads the XLSX report.
     *
     * @param {Object} action - The action data for downloading.
     */
    async downloadXlsx(action) {
        if (action['data']['output_format']) {
            BlockUI;
            await download({
                url: '/inventory_dynamic_xlsx_reports',
                data: action.data,
                complete: () => unblockUI,
                error: (error) => self.call('crash_manager', 'rpc_error', error),
            });
        }
    }
}
InventoryReport.template = "InventoryReport"
registry.category("actions").add("inv_r", InventoryReport)
