/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { dialogService } from "@web/core/dialog/dialog_service";
import { MasterSearchDialog } from "./MasterSearchDialog"
const { Component} = owl;

export class SearchBarSystray extends Component {

  // Component for the search bar in the systray.
  setup() {
    this.dialogService = useService("dialog")
  }
  onSearchIconClick() {
//    // Handle clicks on the search icon.
    this.dialogService.add(MasterSearchDialog)
  }
}
SearchBarSystray.template = "master_search_systray.SearchBarSystray";
export const systrayItem = { Component: SearchBarSystray, };
registry.category("systray").add("SearchBar", systrayItem, { sequence: 1,});
