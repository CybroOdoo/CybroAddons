/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
const actionRegistry = registry.category("actions");
import { uiService } from "@web/core/ui/ui_service";
import { renderToElement } from "@web/core/utils/render";

//  Extending components for adding purchase report class
class PosReport extends Component {
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
            wizard_id : [],
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
                this.state.wizard_id = await this.orm.create("pos.report",[{}]);
                }
            this.state.data = await this.orm.call("pos.report", "pos_report", [this.state.wizard_id]);
            this.state.order_line = this.state.data.report_lines
        }
        catch (el) {
            window.location.href
        }
    }
    async print_pdf(e) {
    //Prints the POS report as a PDF.
			e.preventDefault();
			return this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'all_in_one_pos_kit.pos_order_report',
            'report_file': 'all_in_one_pos_kit.pos_order_report',
            'data': {
                'report_data': this.state.data
            },
            'context': {
						'active_model': 'pos.report',
						'landscape': 1,
						'pos_order_report': true
					},
			'display_name': 'PoS Order',
        });
		}
	async print_xlsx() {
	//Prints the POS report as an XLSX file.
        var data = this.state.data
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
				this.uiService.block();
				await download({
            url: '/pos_dynamic_xlsx_reports',
            data: action.data,
            complete: this.uiService.unblock(),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
          });
		}
    async button_view_order (event) {//Opens a POS order in a new window.
        event.preventDefault();
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: 'pos.order',
            res_id: parseInt(event.target.id),
            views: [[false, "form"]],
            target: "current",
        });

    }
    async apply_filter(ev) {
    //Applies the selected filters and reloads the POS report data.
			this.initial_render = false;
			let filter_data_selected = {};
			this.state.order_by = this.order_by.el.value
			filter_data_selected.date_from = this.start_date.el.value
            filter_data_selected.date_to = this.end_date.el.value
            filter_data_selected.report_type = this.state.order_by
			let data = await this.orm.write("pos.report",this.state.wizard_id, filter_data_selected);
            this.load_data(this.initial_render)
		}
    }
    PosReport.template = 'PosReport';
actionRegistry.add("pos_r", PosReport);
