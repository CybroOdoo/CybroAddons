/** @odoo-module */
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useSetupView } from "@web/views/view_hook";

patch(FormController.prototype,'FormController', {
/* Patch FormController to restrict auto save in form views */
   setup(){
      this._super();
      this.uiService = useService("ui");
      this.beforeLeaveHook = false
      useSetupView({
          beforeLeave: () => this.beforeLeave(),
          beforeUnload: (ev) => this.beforeUnload(ev),
      });
   },
   async beforeLeave() {
   /* function will work before leave the form */
      if(this.model.root.isDirty &&  this.beforeLeaveHook == false){
          if (confirm("Do you want to save changes before leaving?")) {
              this.model.root.save({noReload: true, stayInEdition: true})
          } else {
              this.model.root.discard();
          }
          this.beforeLeaveHook = true
      }
   },
   beforeUnload: async (ev) => {
       ev.preventDefault();
   }
});
