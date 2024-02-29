/** @odoo-module */
/* Import necessary modules and components */
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement, renderToFragment } from "@web/core/utils/render";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
const actionRegistry = registry.category("actions");

/* Define a new component named 'PosReport' */
export class PosReport extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.root = useRef('root-PosReport')
        this.wizard_id = this.props.action.context.wizard | null;
        onMounted(() => {
            this.start_function()
        })
    }
//    Start Function
    start_function() {
        var self = this;
        self.initial_render = true;
        this.orm.call('pos.report', 'create', [{}]).then((res) => {
            self.wizard_id = res;
            self.load_data(self.initial_render);
            self.apply_filter();
        })
    }
//    Load Data function to load the data
	load_data(initial_render = true) {
	    var self = this;
	    self.orm.call('pos.report', 'pos_report', [this.wizard_id]).then((datas) => {
            if(datas['orders']) {
                $(this.root.el.querySelector('.table_view_pr')).empty();
                this.root.el.querySelector('.table_view_pr').append(renderToFragment('PosOrderTable', {
                    filter: datas['filters'],
                    order: datas['orders'],
                    report_lines: datas['report_lines'],
                    main_lines: datas['report_main_line']
                }));
            }
	    })
	}
//    Function to print the PDF report
    print_pdf(e) {
        e.preventDefault();
        var self = this;
        this.orm.call('pos.report', 'pos_report', [[self.wizard_id]]).then((data) => {
            var action = {
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': 'pos_report_generator.pos_order_report',
                'report_file': 'pos_report_generator.pos_order_report',
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
            return this.env.services.action.doAction(action);
        })
	}
//    Function to print the xlsx report
	print_xlsx() {
        var self = this;
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
//	xlsx download function
	downloadXlsx (action) {
	    BlockUI;
	    download({
           url: '/pos_dynamic_xlsx_reports',
           data: action.data,
           complete: () => unblockUI,
           error: (error) => self.call('crash_manager', 'rpc_error', error),
	    });
	}
//	Function to apply the filters
    apply_filter() {
        var self = this;
        var filter_data_selected = {};
         // Get the value of the date_from input element
        if(this.root.el.querySelector('.date_from').value) {
            filter_data_selected.date_from = this.root.el.querySelector('.date_from').value
        }
        if(this.root.el.querySelector('.date_to').value){
            filter_data_selected.date_to = this.root.el.querySelector('.date_to').value
        }
        self.initial_render = false;
        if ($(this.root.el.querySelector('.report_type')).length) {
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
        self.orm.call('pos.report', 'write', [self.wizard_id, filter_data_selected]).then((res) => {
            self.initial_render = false;
			self.load_data(self.initial_render);
        })
    }
}
PosReport.template = "PosReport";
actionRegistry.add('pos_r', PosReport);
