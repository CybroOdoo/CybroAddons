/** @odoo-module **/
import { session } from "@web/session";
import { SearchModel } from "@web/search/search_model";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";

let cachedCustomModels = null;

function isFeatureEnabled() {
    return Boolean(session.is_hide_filters_groupby_enabled && session.is_hide_filters_groupby_enabled !== "False");
}

async function getCustomModels(orm) {
    if (session.hide_filters_groupby_models && session.hide_filters_groupby_models.length) {
        return session.hide_filters_groupby_models;
    }
    if (cachedCustomModels !== null) {
        return cachedCustomModels;
    }
    try {
        const allowedIds = JSON.parse(session.ir_model_ids || "[]");
        if (!allowedIds.length || !orm) {
            cachedCustomModels = [];
            return cachedCustomModels;
        }
        const records = await orm.searchRead("ir.model", [["id", "in", allowedIds]], ["model"]);
        cachedCustomModels = records.map((r) => r.model);
        return cachedCustomModels;
    } catch {
        cachedCustomModels = [];
        return cachedCustomModels;
    }
}

function shouldHideForModelSync(resModel) {
    if (!isFeatureEnabled()) {
        return false;
    }
    if (session.hide_filters_groupby === "global") {
        return true;
    }
    if (session.hide_filters_groupby === "custom") {
        const customModels = session.hide_filters_groupby_models || cachedCustomModels || [];
        return Boolean(resModel && customModels.includes(resModel));
    }
    return false;
}

// -----------------------------------------------------------
// Patch SearchModel: Clear searchMenuTypes for targeted models
// -----------------------------------------------------------
patch(SearchModel.prototype, {
    async load(config) {
        await super.load(...arguments);
        if (!isFeatureEnabled()) {
            return;
        }
        if (session.hide_filters_groupby === "global") {
            this.searchMenuTypes.clear();
        } else if (session.hide_filters_groupby === "custom") {
            const customModels = await getCustomModels(this.env.services.orm);
            if (this.resModel && customModels.includes(this.resModel)) {
                this.searchMenuTypes.clear();
            }
        }
    },
});

// -----------------------------------------------------------
// Patch SearchBar: Only prevent onSearchClick on targeted models
// -----------------------------------------------------------
patch(SearchBar.prototype, {
    onSearchClick() {
        const resModel = this.env.searchModel?.resModel;
        if (!shouldHideForModelSync(resModel)) {
            super.onSearchClick(...arguments);
        }
    },
});
