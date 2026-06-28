/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MasterSearchDialog } from "./MasterSearchDialog"

export class SearchBarSystray extends Component {

  setup() {
    this.dialogService = useService("dialog")
  }
  onSearchIconClick() {
    this.dialogService.add(MasterSearchDialog)
  }
}
SearchBarSystray.template = "master_search_systray.SearchBarSystray";
export const systrayItem = { Component: SearchBarSystray, };
registry.category("systray").add("SearchBar", systrayItem, { sequence: 1,});
