import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import {
    X2ManyField,
    x2ManyField,
} from "@web/views/fields/x2many/x2many_field";
import { ListRenderer } from "@web/views/list/list_renderer";

export class FieldMany2ManyAltSosRenderer extends ListRenderer {
   isCurrentRecord(record) {
      return record.resId === this.props.list.model.root.resId;
  }
}
FieldMany2ManyAltSosRenderer.recordRowTemplate =
    "tender_management_sales.AltSOsListRenderer.RecordRow";

export class FieldMany2ManyAltSOs extends X2ManyField {
   setup() {
      super.setup();
      this.orm = useService("orm");
      this.action = useService("action");
   }

   get isMany2Many() {
      return true;
   }

   /**
    * Override to: avoid reopening currently open record
    *              open record in same window w/breadcrumb extended
    * @override
    */
   async openRecord(record) {
      if (record.resId !== this.props.record.resId) {
         await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: record.resModel,
            res_id: record.resId,
            views: [[false, "form"]],
            target: "current",
            context: this.props.context,
        });
      }
   }
}

FieldMany2ManyAltSOs.components = {
   ...X2ManyField.components,
   ListRenderer: FieldMany2ManyAltSosRenderer,
};

export const fieldMany2ManyAltSOs = {
    ...x2ManyField,
    component: FieldMany2ManyAltSOs,
};
registry.category("fields").add("many2many_alt_sos", fieldMany2ManyAltSOs);
