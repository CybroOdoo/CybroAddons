/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, signal, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
import { download } from "@web/core/network/download";

export class InventoryReport extends Component {
    static template = "InventoryReport";

    table_view_pr = signal.ref();
    date_from = signal.ref();
    date_to = signal.ref();
    report_type = signal.ref();
    report_res = signal.ref();
    dates = signal.ref();

    /**
     * Initializes the InventoryReport component.
     */
    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
        this.companyService = useService("company");
        this.initial_render = false;
        this.selected_report_type = 'report_by_transfers';

        onMounted(async () => {
            this.initial_render = true;
            try {
                const res = await rpc('/web/dataset/call_kw/dynamic.inventory.report/create', {
                    model: 'dynamic.inventory.report',
                    method: 'create',
                    args: [{}],
                    kwargs: {},
                });
                this.wizard_id = res;
                await this.load_data(this.initial_render);
                this.apply_filter();
            } catch (error) {
                this.notification.add(_t("Could not initialize inventory report: %s", error.message || error), {
                    type: "danger",
                });
            }
        });
    }

    /**
     * Handles selection of a report type from the dropdown.
     *
     * @param {Event} e - The event object.
     * @param {string} value - The report type key.
     * @param {string} label - The report type display label.
     */
    on_select_report_type(e, value, label) {
        if (e) e.preventDefault();
        this.selected_report_type = value;
        const reportTypeEl = this.report_type();
        if (reportTypeEl) {
            reportTypeEl.value = value;
        }
        const reportResEl = this.report_res();
        if (reportResEl) {
            reportResEl.innerHTML = label;
        }
        this.apply_filter();
    }

    /**
     * Loads data for the report.
     *
     * @param {boolean} initial_render - Indicates if it's the initial render.
     */
    async load_data(initial_render = true) {
        if (!this.wizard_id) return;
        try {
            const datas = await rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
                model: 'dynamic.inventory.report',
                method: 'inventory_report',
                args: [
                    [this.wizard_id]
                ],
                kwargs: {},
            });
            const tableEl = this.table_view_pr();
            if (datas && datas['orders'] && tableEl) {
                if (!datas['orders']['company_id'] && this.companyService && this.companyService.currentCompany) {
                    datas['orders']['company_id'] = this.companyService.currentCompany.id;
                }
                tableEl.innerHTML = '';
                const rendered = renderToElement('InventoryReportTable', {
                    filter: datas['filters'],
                    order: datas['orders'],
                    report_lines: datas['report_lines'],
                    main_lines: datas['report_main_line'],
                    this: this,
                    button_view_order: (ev) => this.button_view_order(ev),
                });
                if (rendered) {
                    tableEl.append(rendered);
                }
            }
        } catch (error) {
            this.notification.add(_t("Could not load inventory report data: %s", error.message || error), {
                type: "danger",
            });
        }
    }

    /**
     * Applies filters to the report.
     */
    apply_filter() {
        if (!this.wizard_id) return;
        this.initial_render = false;
        const filter_data_selected = {};

        const dateFromEl = this.date_from();
        const dateToEl = this.date_to();
        const datesEl = this.dates();

        if (dateFromEl && dateFromEl.value) {
            filter_data_selected.date_from = dateFromEl.value;
            if (datesEl) {
                datesEl.innerHTML = dateFromEl.value;
            }
        }
        if (dateToEl && dateToEl.value) {
            filter_data_selected.date_to = dateToEl.value;
            if (datesEl) {
                datesEl.innerHTML = dateToEl.value;
            }
        }
        if (filter_data_selected.date_from && filter_data_selected.date_to) {
            if (datesEl) {
                datesEl.innerHTML = filter_data_selected.date_from + " to " + filter_data_selected.date_to;
            }
        }
        const reportTypeEl = this.report_type();
        const selectedType = (reportTypeEl && reportTypeEl.value) || this.selected_report_type || 'report_by_transfers';
        filter_data_selected.report_type = selectedType;

        const reportLabels = {
            'report_by_transfers': 'Report By Transfers',
            'report_by_categories': 'Report By Categories',
            'report_by_warehouse': 'Report By Warehouse',
            'report_by_location': 'Report By Location',
        };
        const reportResEl = this.report_res();
        if (reportResEl) {
            reportResEl.innerHTML = reportLabels[selectedType] || selectedType;
        }
        rpc('/web/dataset/call_kw/dynamic.inventory.report/write', {
            model: 'dynamic.inventory.report',
            method: 'write',
            args: [this.wizard_id, filter_data_selected],
            kwargs: {},
        }).then(() => {
            this.initial_render = false;
            this.load_data(this.initial_render);
        });
    }

    /**
     * Resets filters.
     */
    reset_filter() {
        const dateFromEl = this.date_from();
        const dateToEl = this.date_to();
        const datesEl = this.dates();
        const reportTypeEl = this.report_type();
        const reportResEl = this.report_res();

        if (dateFromEl) dateFromEl.value = '';
        if (dateToEl) dateToEl.value = '';
        if (datesEl) datesEl.innerHTML = '';
        this.selected_report_type = 'report_by_transfers';
        if (reportTypeEl) reportTypeEl.value = 'report_by_transfers';
        if (reportResEl) reportResEl.innerHTML = 'Report By Transfers';
        this.apply_filter();
    }

    /**
     * Prints the report as a PDF.
     *
     * @param {Event} e - The event object.
     */
    print_pdf(e) {
        if (e) e.preventDefault();
        if (!this.wizard_id) return;
        rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
            model: 'dynamic.inventory.report',
            method: 'inventory_report',
            args: [
                [this.wizard_id]
            ],
            kwargs: {},
        }).then((data) => {
            const action = {
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'inventory_report_generator.inventory_pdf_report',
                report_file: 'inventory_report_generator.inventory_pdf_report',
                data: {
                    report_data: data
                },
                context: {
                    active_model: 'dynamic.inventory.report',
                    landscape: 1,
                    inventory_pdf_report: true
                },
                display_name: 'Inventory Report',
            };
            return this.action.doAction(action);
        });
    }

    /**
     * Opens a view for a specific order.
     *
     * @param {Event} ev - The event object.
     * @param {number|string} [orderId] - Optional order ID.
     */
    button_view_order(ev, orderId) {
        if (ev) ev.preventDefault();
        const rawId = orderId || (ev && ev.target && (ev.target.id || ev.target.dataset.id || ev.target.getAttribute('id')));
        const id = parseInt(rawId, 10);
        if (!id) return;
        this.action.doAction({
            name: _t("Transfer Order"),
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            res_id: id,
            views: [
                [false, 'form']
            ],
            target: 'current'
        });
    }

    /**
     * Event delegation for table clicks (e.g. view transfer order).
     */
    onTableViewClick(ev) {
        const transferLink = ev.target.closest('.view_transfer_order');
        if (transferLink) {
            this.button_view_order(ev, transferLink.getAttribute('id'));
        }
    }

    /**
     * Exports the report data as an XLSX file.
     */
    print_xlsx() {
        if (!this.wizard_id) return;
        rpc('/web/dataset/call_kw/dynamic.inventory.report/inventory_report', {
            model: 'dynamic.inventory.report',
            method: 'inventory_report',
            args: [
                [this.wizard_id]
            ],
            kwargs: {},
        }).then((data) => {
            const action = {
                data: {
                    model: 'dynamic.inventory.report',
                    options: JSON.stringify(data['orders']),
                    output_format: 'xlsx',
                    report_data: JSON.stringify(data['report_lines']),
                    report_name: 'Inventory Report',
                    dfr_data: JSON.stringify(data),
                },
            };
            this.downloadXlsx(action);
        });
    }

    /**
     * Downloads the XLSX report.
     *
     * @param {Object} action - The action data for downloading.
     */
    async downloadXlsx(action) {
        if (action && action.data && action.data.output_format) {
            await download({
                url: '/inventory_dynamic_xlsx_reports',
                data: action.data,
            });
        }
    }
}

registry.category("actions").add("inv_r", InventoryReport);
