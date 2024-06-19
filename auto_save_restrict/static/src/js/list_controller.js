/** @odoo-module */
import { ListController } from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { useSetupView } from "@web/views/view_hook";

patch(ListController.prototype,'FormController', {
/* Patch ListController to restrict auto save in tree views */
   setup(){
      this._super();
      useSetupView({
          beforeLeave: () => this.beforeLeave(),
          beforeUnload: (ev) => this.beforeUnload(ev),
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
   },
   beforeUnload: async (ev) => {
       ev.preventDefault();
   }
});
