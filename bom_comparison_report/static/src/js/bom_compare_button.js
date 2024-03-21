/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class BomList extends ListController {
   setup() {
       super.setup();
   }
   ShowWizard() {
       this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'bom.comparison',
          name:'Open Wizard',
          view_mode: 'form',
          view_type: 'form',
          views: [[false, 'form']],
          target: 'new',
      });
   }
}
registry.category("views").add("compare_button_tree", {
   ...listView,
   Controller: BomList,
   buttonTemplate: "bom_comparison_report.ListView.Buttons",
});