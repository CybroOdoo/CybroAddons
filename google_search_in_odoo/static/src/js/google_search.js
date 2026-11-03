import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export class GoogleSearchWidget extends Component {
    static template = "google_search_in_odoo.SearchSystray";

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.searchInputRef = useRef("searchInput");
        this.state = useState({
            isGoogleSearchEnabled: false,
            showResults: false,
            query: "",
            results: [],
            expandedIndices: {},
        });

        onWillStart(async () => {
            await this._checkSearchStatus();
        });
    }

    async _checkSearchStatus() {
        try {
            const isEnabled = await this.orm.call(
                "res.users",
                "get_google_search_status",
                []
            );
            this.state.isGoogleSearchEnabled = Boolean(isEnabled);
        } catch {
            this.state.isGoogleSearchEnabled = false;
        }
    }

    onKeyPress(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this._onSearch();
        }
    }

    _onCloseResults(ev) {
        if (ev) {
            ev.stopPropagation();
        }
        this.state.showResults = false;
    }

    toggleExpand(index) {
        this.state.expandedIndices[index] = !this.state.expandedIndices[index];
    }

    async _onSearch() {
        const query = (this.state.query || "").trim();
        if (!query) {
            this.state.showResults = false;
            return;
        }

        try {
            const result = await this.orm.call(
                "res.users",
                "google_search_config",
                [query]
            );

            if (!result) {
                this.dialog.add(WarningDialog, {
                    title: _t("Warning"),
                    message: _t("Limit exceeded for Queries and Queries per day"),
                });
                return;
            }

            if (result.error) {
                this.dialog.add(WarningDialog, {
                    title: _t("Alert"),
                    message: result.error,
                });
                return;
            }

            if (Array.isArray(result)) {
                this.state.results = result;
                this.state.expandedIndices = {};
                this.state.showResults = true;
            }
        } catch {
            this.dialog.add(WarningDialog, {
                title: _t("Alert"),
                message: _t("Unable to perform search. Please try again later."),
            });
        }
    }
}

export const searchItem = {
    Component: GoogleSearchWidget,
};

registry.category("systray").add("GoogleSearch", searchItem, { sequence: 0 });
