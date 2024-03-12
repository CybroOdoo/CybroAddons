/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const { Component, useRef, onMounted ,useState } = owl

export class SaleReport extends Component {
    setup(){
        this.state = useState({
            rpt_type: 'report_by_order',
            data:{},
            })
            this.action = useService("action");
            this.ReportRes = useRef('ReportRes');
            this.ReportType = useRef('ReportType');
            this.DateFrom = useRef('DateFrom');
            this.DateTo = useRef('DateTo');
            this.orm = useService("orm");
            onMounted(async()=> {
                await this.FetchData();
            })
    }
    async FetchData(){
    /* Function for fetching datas */
        const id = await this.orm.call("sales.report", "create", [{}]);
        this.state.id = id
        this.state.data = await this.orm.call('sales.report','sale_report',[id])
    }
    async ChangeReportType(){
    /* Function for changing report type */
        this.ReportRes.el.innerHTML= this.state.rpt_type
    }
    async apply_filter(){
    /* Function for applying various filters */
        var filter_data_selected = {};
        if (this.DateFrom.el.value){
            filter_data_selected.date_from = this.DateFrom.el.value + ' 00:00:00'
        }
        if (this.DateTo.el.value){
            filter_data_selected.date_to = this.DateTo.el.value + ' 00:00:00'
        }
        filter_data_selected.report_type = this.state.rpt_type
        await this.orm.call('sales.report', 'write', [this.state.id, filter_data_selected])
        this.state.data = await this.orm.call('sales.report','sale_report',[this.state.id])
    }
    print_pdf(){
    /* Function for Printing pdf */
        this.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'all_in_one_sales_kit.sale_order_report',
            'report_file': 'all_in_one_sales_kit.sale_order_report',
            'data': {
                'report_data': this.state.data
            },
            'context': {
                'active_model': 'sales.report',
                'landscape': 1,
                'sale_order_report': true
            },
            'display_name': 'Sale Order',
        });
    }
    print_xlsx() {
    /* Function for Printing xlsx */
        var self = this;
        var action = {
            'data': {
                'model': 'sales.report',
                'options': JSON.stringify(this.state.data),
                'output_format': 'xlsx',
                'report_name': 'Sale Report',
            },
        };
        self.downloadXlsx(action);
    }
    async downloadXlsx(action){
    /* It is to pass data needed to print xlsx report */
    BlockUI;
        await download({
           url: '/xlsx_reports',
           data: action.data,
           complete: () => unblockUI,
           error: (error) => self.call('crash_manager', 'rpc_error', error),
       });
    }

}
SaleReport.template = "SaleReport"
registry.category("actions").add('s_r', SaleReport)
