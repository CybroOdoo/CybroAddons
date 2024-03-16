/** @odoo-module */
import { ListController } from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { useSetupView } from "@web/views/view_hook";

patch(ListController.prototype, {
/* Patch ListController to restrict auto save in tree views */
   setup(){
      super.setup(...arguments);
      useSetupView({
          beforeLeave: () => this.beforeLeave(),
      });
   },
   async beforeLeave() {
   /* function will work before leave the list */
      if(this.model.root.editedRecord){
          if (confirm("Do you want to save changes before leaving?")) {
          } else {
              this.onClickDiscard();
          }
      }
   }
});
