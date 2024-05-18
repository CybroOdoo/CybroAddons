/** @odoo-module **/
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { useService } from "@web/core/utils/hooks";
import { Component,useState } from "@odoo/owl";
import { session } from "@web/session";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
export class GoogleSearchWidget extends Component {
      async setup() {
      super.setup(...arguments);
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.events = [
                'keydown',
            ];
        this.state = useState({
      isGoogleSearchEnabled: '',
      });
      this.orm.call("ir.config_parameter", "get_param", ["google_search_in_odoo.google_search"]).then((result) => {
      this.state.isGoogleSearchEnabled = result;
      console.log("Google search is enabled:", this.state.isGoogleSearchEnabled);
      });
      };
     onKeyPress(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this._onClick(ev);
        }
    }
    async _onClick(ev) {
            var self = this
        // Get response from google based on the search value and display result on the template
        var input = document.getElementById("search_text")
        const resultsDiv = document.getElementById('google_result');
        if (ev.key === "Enter" && input.value.trim() !== '') {
         this.orm.call('res.config.settings','google_search_config',[input.value]
        ).then(function (result) {
        if (result.error) {
        var title = _t("Alert");
        var message = _t(result.error);
           self.dialog.add(WarningDialog, { title, message });
                } else if (result === null) {
                var warning = _t('Limit exceeded for Queries and Queries per day')
                    self.dialog.add(WarningDialog, { title, warning });
                }else {
                    resultsDiv.innerHTML = '';
                    for (let i = 0; i < result.length; i++) {
                        const resultItem = document.createElement("div");
                        const titleText = document.createTextNode(result[i].title);
                        const titleElement = document.createElement("h2");
                        titleElement.classList.add("header")
                        titleElement.appendChild(titleText);
                        const linkElement = document.createElement("a");
                        linkElement.classList.add("link")
                        linkElement.href = result[i].link;
                        linkElement.textContent = result[i].link;
                        const snippetText = document.createTextNode(result[i].snippet);
                        const snippetElement = document.createElement("p");
                        snippetElement.classList.add("content")
                        snippetElement.appendChild(snippetText);
                        resultItem.appendChild(titleElement);
                        resultItem.appendChild(linkElement);
                        resultItem.appendChild(snippetElement);
                        resultsDiv.appendChild(resultItem);
                    }
                    resultsDiv.style.display = 'block';
                }
                 });
        } else {
            resultsDiv.style.display = 'none';
        }
        }
    }
GoogleSearchWidget.components = { Dropdown };
    export const searchItem = {
    Component: GoogleSearchWidget,
};
GoogleSearchWidget.template = "google_search_in_odoo.SearchSystray"
registry.category("systray").add("GoogleSearch", searchItem, { sequence: 0 });
