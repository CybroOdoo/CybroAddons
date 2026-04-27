/** @odoo-module **/

import { Popover } from "@web/core/popover/popover";
import { session } from "@web/session";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { hasTouch } from "@web/core/browser/feature_detection";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

// ----------------------------------------
// Patch SearchBar: Remove onSearchClick logic
// ----------------------------------------

patch(SearchBar.prototype, {
    onSearchClick() {
        // Only override when feature is enabled
        if (session.is_hide_filters_groupby_enabled !== "True") {
            if (!hasTouch()) {
                if (!this.inputRef.el.value.length) {
                    this.searchBarDropdownState.open();
                } else {
                    this.inputDropdownState.open();
                }
            }
        }
    },
});

// ----------------------------------------
// Patch ControlPanel: Hide Filters/GroupBy
// ----------------------------------------

patch(ControlPanel.prototype, {
    setup() {
        super.setup();

        if (session.is_hide_filters_groupby_enabled !== "True") {
            return;
        }

        if (session.hide_filters_groupby === "global") {
            onMounted(() => {
                this.hideGlobally();
                this.observeMutations();
            });
        } else if (session.hide_filters_groupby === "custom") {
            onMounted(() => this.hideOnCustom());
        }

        // Cleanup observer when component destroyed
        onWillUnmount(() => {
            if (this._observer) {
                this._observer.disconnect();
                this._observer = null;
            }
        });
    },

    // ----------------------------------------
    // GLOBAL MODE
    // ----------------------------------------
    hideGlobally() {
        const toggler = document.querySelector(".o_searchview_dropdown_toggler");
        const searchWrapper = document.querySelector(".o_cp_searchview");

        if (toggler) toggler.style.display = "none";

        // Fix outer border so it closes properly
        if (searchWrapper) {
            searchWrapper.style.setProperty("border", "1px solid #ccc", "important");
            searchWrapper.style.setProperty("border-radius", "5px", "important");
            searchWrapper.style.setProperty("overflow", "hidden", "important");
        }
    },
    

    observeMutations() {
        if (this._observer) {
            this._observer.disconnect();
        }

        // Run immediately
        this.hideGlobally();

        this._observer = new MutationObserver(() => {
            this.hideGlobally();
        });

        this._observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    },

    // ----------------------------------------
    // CUSTOM MODE
    // ----------------------------------------
    async hideOnCustom() {
        const sm = this.env.searchModel;
        if (!sm) return;

        const resModel = sm.resModel;
        if (!resModel) return;

        // get model id
        const modelIds = await this.env.services.orm.search(
            "ir.model",
            [["model", "=", resModel]],
            { limit: 1 }
        );

        const modelId = modelIds[0];

        // convert session list safely
        const allowedIds = JSON.parse(session.ir_model_ids || "[]");

        if (allowedIds.includes(modelId)) {
            this.hideGlobally();
            this.observeMutations();
        }
    },
});



