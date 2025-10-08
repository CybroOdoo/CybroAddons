/** @odoo-module **/
import { Component, useRef, useExternalListener, useState} from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
let nextItemId = 1;

export class MasterSearchDialog extends Component {
    setup() {
        // Set up the initial state and services.
        this.state = useState({
          focusedIndex: 0,
          menu_list: [],
          result: null,
          query: "",
          isSearchVisible: false, // Add a state variable to control visibility
        });
        this.orm = useService("orm");
        this.inputRef = !this.props.autofocus ? useRef("autofocus") : useAutofocus();
        this.items = useState([]);
        this.rpc = useService("rpc");
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.dialogService = useService("dialog")
        useExternalListener(window, "click", this.onWindowClick);
        useExternalListener(window, "keydown", this.onWindowKeydown);
    }

    toggleSearchVisibility() {
    // Toggle the visibility of the search bar.
    this.state.isSearchVisible = !this.state.isSearchVisible;
    }

    selectItem(item) {
        this.props.close()
        // Handle the selection of an item in the search results.
        if (item.isChild) {
          this.state.isSearchVisible = false;
          this.actionService.doAction(
            {
              res_model: item.model,
              res_id: item.rec_id,
              target: "current",
              type: "ir.actions.act_window",
              views: [[false, "form"]],
            },
          );
        } else {
          this.resetState();
        }
    }

    async computeState(options = {}) {
    // Compute the state based on the provided options.
        const query = "query" in options ? options.query : this.state.query;
        const focusedIndex = "focusedIndex" in options ? options.focusedIndex : this.state.focusedIndex;
        this.state.query = query;
        this.state.focusedIndex = focusedIndex;
        this.inputRef.el.value = query;
        const result = await this.rpc("/master/search", {
          query: query,
        });
        const trimmedQuery = this.state.query.trim();
        this.items.length = 0;
        if (!trimmedQuery) {
          this.render();
          return;
        }
        if (result.length != 0) {
          for (const record of result) {
            var temp_items = [];
            for (const rec of record) {
                temp_items.push({
                    id: nextItemId++,
                    name: rec.name,
                    title: rec.title,
                    rec_id: rec.id,
                    isChild: rec.isChild,
                    isParent: rec.isParent,
                    model: rec.model,
                });
            }
            this.items.push(temp_items);
          }
          this.render();
        } else {
          this.items = [];
          this.render();
        }
    }

    resetState() {
        // Reset the state of the search bar.
        this.computeState({
          focusedIndex: 0,
          query: "",
        });
        this.inputRef.el.focus();
    }

    // * Handles the search input event.
    //This method is triggered when the user types in the search input field. It fetches
    //* the menu items and records results based on the query and updates the state with the
    //* combined results. If the query is empty, it resets the state and clears the items.
    async onSearchInput(ev) {
        const query = this.inputRef.el.value;
        if (query.trim()) {
            const [menuItems, serverResults] = await Promise.all([
                this.fetchMenuItems(query),
                this.fetchServerResults(query),

            ]);
            this.state.items = [...menuItems, ...serverResults];
            this.computeState({
                query,
                focusedIndex: 0,
            });
        } else if (this.items.length) {
            this.resetState();
            this.state.items = [];
        }
    }


    async fetchMenuItems(query) {
    //Fetches menu items based on the query.
    //This method searches through the available menu items and filters them
    //based on the query string. It returns a list of matching menu items.
        const app_list = this.menuService.getAll();
        const menu_list = [];
        const apps = this.menuService.getApps();
        let app_name = "";
        for (const app_list_item of app_list) {
            if (
                app_list_item.id !== "root" &&
                app_list_item.actionModel !== false &&
                app_list_item.name.toLowerCase().match(new RegExp(query.trim().toLowerCase().replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&')))
            ) {
                const app = apps.find((app) => app.appID === app_list_item.appID);
                if (app) {
                    app_name = app.name;
                }
                menu_list.push({
                    id: app_list_item.id,
                    name: `${app_name}/${app_list_item.name}`,
                    actionModel: app_list_item.actionModel,
                    class: "",
                });
            }
        }
        return menu_list;
    }
    async fetchServerResults(query) {
        // * Fetches search results from the records based on the query.
        const result = await this.rpc("/master/search", {
            query: query,
        });

        const trimmedQuery = query.trim();
        const serverResults = [];

        if (!trimmedQuery) {
            return serverResults;
        }

        if (result.length !== 0) {
            for (const record of result) {
                const temp_items = [];
                for (const rec of record) {
                    temp_items.push({
                        id: nextItemId++,
                        name: rec.name,
                        title: rec.title,
                        rec_id: rec.id,
                        isChild: rec.isChild,
                        isParent: rec.isParent,
                        model: rec.model,
                    });
                }
                serverResults.push(temp_items);
            }
        }
        return serverResults;
    }

    onWindowClick(ev) {
        this.props.close()
        // Handle clicks on the window.
        if (this.items.length) {
          this.resetState();
        }
    }
    onWindowKeydown(ev) {
        // Check if the pressed key is the "Esc" key
        if (ev.key === "Escape") {
            this.onClickMenu();
        }
    }
    onClickMenu() {
        this.props.close()
  }
  onSearchIconClick() {
    // Handle clicks on the search icon.
    this.dialogService.add(MasterSearchDialog)
    this.toggleSearchVisibility();
  }
  onCLickMasterModal(ev){
    ev.stopPropagation()
  }
  closeSearch() {
    // Close the search bar.
    this.state.isSearchVisible = false;
  }
}

MasterSearchDialog.template = "master_search_systray.MasterSearchDialog"
MasterSearchDialog.components = { Dialog }