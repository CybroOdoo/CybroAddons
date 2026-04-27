/** @odoo-module **/
import { Component, useState, useRef } from "@odoo/owl";
import { session } from "@web/session";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class InventoryReport extends Component{
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
               order_by : 'report_by_transfers',
               wizard_id : []
           });
            this.load_data();
      }
      /** Gets values using rpc query */
      async load_data(wizard_id = null) {
       /**
        * Loads the data for the purchase report.
        */
        try {
            if(wizard_id == null){
                this.state.wizard_id = await this.orm.create("dynamic.inventory.report",[{}]);
                }
            this.state.data = await this.orm.call("dynamic.inventory.report", "inventory_report", [this.state.wizard_id]);
            this.state.order_line = this.state.data.report_lines
        }
        catch (el) {
            window.location.href
        }
   }
   /** Filter applying function */
   async applyFilter(ev) {
       let filter_data = {}
       this.state.order_by = this.order_by.el.value
       filter_data.date_from = this.start_date.el.value
       filter_data.date_to = this.end_date.el.value
       filter_data.report_type = this.order_by.el.value
       let data = await this.orm.write("dynamic.inventory.report",this.state.wizard_id, filter_data);
       this.load_data(this.state.wizard_id)
   }
    /** Print pdf report */
   async printPdf(ev) {
         ev.preventDefault();
         var self = this;
         var action_title = self.props.action.display_name;
         return self.action.doAction({
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
       var data = this.state.data
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
       this.uiService.block();
       await download({
           url: '/xlsx_reports',
           data: action.data,
           complete: this.uiService.unblock(),
           error: (error) => this.call('crash_manager', 'rpc_error', error),
         });
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
InventoryReport.template = 'InventoryReport';
registry.category("actions").add("inv_r", InventoryReport);
