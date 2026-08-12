/** @odoo-module */
import { ListRenderer } from "@web/views/list/list_renderer";

export class FieldMany2ManyAltSosRenderer extends ListRenderer {
   isCurrentRecord(record) {
      return record.resId === this.props.list.model.root.resId;
  }
}
