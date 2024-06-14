/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MasterSearchDialog } from "./MasterSearchDialog"

export class SearchBarSystray extends Component {

  // Component for the search bar in the systray.
  setup() {
    this.dialogService = useService("dialog")
  }
  onSearchIconClick() {
    // Handle clicks on the search icon.
    this.dialogService.add(MasterSearchDialog)
  }
}
SearchBarSystray.template = "master_search_systray.SearchBarSystray";
export const systrayItem = { Component: SearchBarSystray, };
registry.category("systray").add("SearchBar", systrayItem, { sequence: 1,});
