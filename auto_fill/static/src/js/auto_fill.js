/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, useState, useExternalListener } from "@odoo/owl";

export class FieldAutoFill extends Component {
    static template = "FieldAutoFill";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        super.setup();
        this.input = useRef("input_data");
        this.container = useRef("container");
        this.rpc = useService("rpc");
        this.dialog = useService("dialog");
        this.state = useState({
            matches: [],
        });

        useInputField({
            getValue: () => this.value,
            refName: "input_data",
        });

        useExternalListener(window, "click", this._onWindowClick.bind(this));
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    _onWindowClick(ev) {
        if (this.container.el && !this.container.el.contains(ev.target)) {
            this.state.matches = [];
        }
    }

    async _onKeyup(ev) {
        if (["Enter", "Tab", "Escape", "ArrowUp", "ArrowDown"].includes(ev.key)) {
            if (ev.key === "Escape") {
                this.state.matches = [];
            }
            return;
        }

        const value = ev.target.value;
        const resModel = this.props.record.resModel;
        const fieldDef = this.props.record.fields[this.props.name];

        if (!fieldDef || fieldDef.type !== "char") {
            this.dialog.add(AlertDialog, {
                body: _t("Only Supported for 'char' type please change field type to 'char'"),
            });
            return;
        }

        if (!value || !value.trim()) {
            this.state.matches = [];
            return;
        }

        try {
            const result = await this.rpc("/matching/records", {
                model: resModel,
                field: this.props.name,
                value: value,
            });
            if (result && result.length > 0) {
                this.state.matches = result.map((r) => (Array.isArray(r) ? r[0] : r));
            } else {
                this.state.matches = [];
            }
        } catch {
            this.state.matches = [];
        }
    }

    async _onSelectRecord(val) {
        this.state.matches = [];
        if (this.input.el) {
            this.input.el.value = val;
        }
        await this.props.record.update({ [this.props.name]: val });
    }
}

export const Fieldautofill = {
    component: FieldAutoFill,
    displayName: _t("Auto Fill"),
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({
        placeholder: attrs.placeholder,
    }),
};

registry.category("fields").add("auto_fill", Fieldautofill);
