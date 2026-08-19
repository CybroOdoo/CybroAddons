/** @odoo-module */

import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, useEffect, onWillStart } from "@odoo/owl";

// Session-level cache: { modelName: { fieldName, fieldTtype } | null }
const recNameCache = {};

/**
 * Fetch and cache the rec.name.config for a given model.
 * Returns { fieldName, fieldTtype } or null.
 */
async function loadConfig(orm, modelName) {
    if (modelName in recNameCache) return recNameCache[modelName];
    try {
        const configs = await orm.searchRead(
            "rec.name.config",
            [["model_name", "=", modelName], ["active", "=", true]],
            ["field_name", "field_ttype"],
            { limit: 1 }
        );
        recNameCache[modelName] = configs.length
            ? { fieldName: configs[0].field_name, fieldTtype: configs[0].field_ttype }
            : null;
    } catch (e) {
        console.warn("rec_name_manager: error loading config for", modelName, e);
        recNameCache[modelName] = null;
    }
    return recNameCache[modelName];
}

/**
 * Given a record read result and a config, return the display string.
 * Handles many2one (returns display_name of related), selection, and plain fields.
 */
function extractDisplayValue(record, config) {
    const val = record[config.fieldName];
    if (val === undefined || val === false || val === null || val === "") return null;
    // many2one: Odoo returns [id, display_name]
    if (config.fieldTtype === "many2one") {
        return Array.isArray(val) ? val[1] : String(val);
    }
    return String(val);
}

// ── Patch FormController to update breadcrumb ───────────────────────────────

import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    async setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this._recNameState = useState({
            customTitle: null,
            originalTitle: null
        });

        onWillStart(async () => {
            await this._loadRecNameConfigForForm();
        });

        useEffect(() => {
            this._updateFormTitle();
        }, () => [this.props.context, this.model.root.data]);
    },

    async _loadRecNameConfigForForm() {
        const modelName = this.model.resModel;
        if (!modelName) return;
        await loadConfig(this.orm, modelName);
    },

    async _updateFormTitle() {
        const modelName = this.model.resModel;
        const recordId = this.model.root.resId;

        if (!modelName || !recordId) return;

        const config = recNameCache[modelName];
        if (!config) {
            this._recNameState.customTitle = null;
            return;
        }

        try {
            const fieldsToRead = [config.fieldName];
            const records = await this.orm.read(modelName, [recordId], fieldsToRead);
            if (records && records[0]) {
                const display = extractDisplayValue(records[0], config);
                if (display) {
                    this._recNameState.customTitle = display;
                } else {
                    this._recNameState.customTitle = null;
                }
            } else {
                this._recNameState.customTitle = null;
            }
        } catch (e) {
            console.warn("rec_name_manager: error updating form title", e);
            this._recNameState.customTitle = null;
        }
    },

    get breadcrumbTitle() {
        if (this._recNameState && this._recNameState.customTitle) {
            return this._recNameState.customTitle;
        }
        return super.breadcrumbTitle;
    },
});

// ── Patch Many2OneField ──────────────────────────────────────────────────────

patch(Many2OneField.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this._recNameState = useState({ customDisplayName: null });

        onWillStart(async () => {
            await this._loadRecNameConfig();
        });

        useEffect(() => {
            this._fetchCustomDisplayName();
        }, () => [this.value]);
    },

    async _loadRecNameConfig() {
        const relation = this.relation;
        if (!relation) return;
        await loadConfig(this.orm, relation);
    },

    async _fetchCustomDisplayName() {
        const relation = this.relation;
        if (!relation) return;

        const config = recNameCache[relation];
        if (!config) {
            this._recNameState.customDisplayName = null;
            return;
        }

        const recordId = this.value && this.value[0];
        if (!recordId) {
            this._recNameState.customDisplayName = null;
            return;
        }

        try {
            const fieldsToRead = [config.fieldName];
            const records = await this.orm.read(relation, [recordId], fieldsToRead);
            if (records && records[0]) {
                const display = extractDisplayValue(records[0], config);
                this._recNameState.customDisplayName = display;
            } else {
                this._recNameState.customDisplayName = null;
            }
        } catch (e) {
            console.warn("rec_name_manager: error fetching custom display name", e);
            this._recNameState.customDisplayName = null;
        }
    },

    get displayName() {
        if (this._recNameState && this._recNameState.customDisplayName !== null) {
            return this._recNameState.customDisplayName;
        }
        return super.displayName;
    },
});