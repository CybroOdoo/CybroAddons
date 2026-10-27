/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { Component, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { renderToFragment } from "@web/core/utils/render";
import { _t } from "@web/core/l10n/translation";

/* Define a new component named 'PosReport' */
export class PosReport extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.ui = useService("ui");
        this.action = useService("action");
        this.root = useRef('root-PosReport')
        this.table = useRef('table-view')
        this.report = useRef('report-type')
        this.wizard_id = null;
        onMounted(() => {
            this.start_function()
        })
    }
    // Start Function
    start_function() {
        var self = this;
        self.initial_render = true;
        this.orm.create('pos.report', [{}]).then((res) => {
            self.wizard_id = res[0];
            self.load_data(self.initial_render);
            self.apply_filter();
        })
    }
    // Load Data function to load the data
	load_data(initial_render = true) {
	    var self = this;
	    self.orm.call('pos.report', 'pos_report', [this.wizard_id]).then((datas) => {
            if(datas['orders']) {
                this.root.el.querySelector('.table_view_pr').innerHTML = '';
                this.root.el.querySelector('.table_view_pr').append(renderToFragment('all_in_one_pos_kit.PosOrderTable', {
                    filter: datas['filters'],
                    order: datas['orders'],
                    report_lines: datas['report_lines'],
                    main_lines: datas['report_main_line']
                }));
            }
	    })
	}
    // Validate the selected date range. Returns true when it is valid.
    validate_dates() {
        const dateFrom = this.root.el.querySelector('.date_from').value;
        const dateTo = this.root.el.querySelector('.date_to').value;
        // The inputs are type="date": an unparsable value comes back empty,
        // so only a complete, well formed range can be compared.
        const isValid = (value) => !value || !isNaN(new Date(value).getTime());
        if (!isValid(dateFrom) || !isValid(dateTo)) {
            this.notification.add(_t("Please enter a valid date."), {
                type: "danger",
            });
            return false;
        }
        if (dateFrom && dateTo && dateFrom > dateTo) {
            this.notification.add(
                _t("The Start Date cannot be later than the End Date."),
                { type: "danger" }
            );
            return false;
        }
        return true;
    }
    // Keep the two date pickers consistent with each other
    on_date_change() {
        const from = this.root.el.querySelector('.date_from');
        const to = this.root.el.querySelector('.date_to');
        to.min = from.value || '';
        from.max = to.value || '';
    }
    // Function to print the PDF report
    print_pdf(e) {
        e.preventDefault();
        if (!this.validate_dates()) {
            return;
        }
        var self = this;
        this.orm.call('pos.report', 'pos_report', [self.wizard_id]).then((data) => {
            var action = {
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': 'all_in_one_pos_kit.pos_order_report',
                'report_file': 'all_in_one_pos_kit.pos_order_report',
                'data': {
                    'report_data': data
                },
                'context': {
                    'active_model': 'pos.report',
                    'landscape': 1,
                    'pos_order_report': true
                },
                'display_name': 'PoS Order',
            };
            return this.action.doAction(action);
        })
	}
    // Function to print the xlsx report
	print_xlsx() {
        var self = this;
        if (!this.validate_dates()) {
            return;
        }
        this.orm.call('pos.report', 'pos_report', [self.wizard_id]).then((data) => {
            var action = {
                'data': {
                    'model': 'pos.report',
                    'options': JSON.stringify(data['orders']),
                    'output_format': 'xlsx',
                    'report_data': JSON.stringify(data['report_lines']),
                    'report_name': 'PoS Report',
                    'dfr_data': JSON.stringify(data),
                },
            };
            self.downloadXlsx(action);
        })
	}
    // Xlsx download function
	async downloadXlsx(action) {
	    this.ui.block();
	    try {
	        await download({
	            url: '/pos_dynamic_xlsx_reports',
	            data: action.data,
	        });
	    } catch (error) {
	        this.notification.add(_t("The XLSX report could not be downloaded."), {
	            type: "danger",
	        });
	    } finally {
	        this.ui.unblock();
	    }
	}
    // Function to apply the filters
    apply_filter() {
        var self = this;
        if (!this.validate_dates()) {
            return;
        }
        var filter_data_selected = {};
        // Always send both dates, a cleared date must remove the old filter
        filter_data_selected.date_from = this.root.el.querySelector('.date_from').value || false;
        filter_data_selected.date_to = this.root.el.querySelector('.date_to').value || false;
        self.initial_render = false;
        if (this.report.el || this.report.getEl?.().length) {
            var report_res = this.root.el.querySelector('#report_res')
            filter_data_selected.report_type = this.root.el.querySelector('.report_type').value
            report_res.value = this.root.el.querySelector('.report_type').value
            if (report_res.value == "report_by_order"){
                report_res.innerHTML = "Report By Order";
            } else if (report_res.value == "report_by_product"){
                report_res.innerHTML = "Report By Product";
            } else if (report_res.value == "report_by_order_detail"){
                report_res.innerHTML = "Report By Order Detail";
            } else if (report_res.value == "report_by_categories"){
                report_res.innerHTML = "Report By Categories";
            } else if (report_res.value == "report_by_salesman"){
                report_res.innerHTML = "Report By Salesman";
            } else {
                report_res.innerHTML = "Report By Payment";
            }
            if (this.root.el.querySelector('.report_type').value == "") {
                report_res.innerHTML = "report_by_order";
            }
        }
        self.orm.write('pos.report', [self.wizard_id], filter_data_selected).then((res) => {
            self.initial_render = false;
			self.load_data(self.initial_render);
        })
    }
}
PosReport.template = "all_in_one_pos_kit.PosReport";
registry.category("actions").add('pos_r', PosReport);
