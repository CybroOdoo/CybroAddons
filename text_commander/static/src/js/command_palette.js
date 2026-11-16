/** @odoo-module **/

import { CommandPalette } from "@web/core/commands/command_palette";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Helper to safely extract display name from ir.model response.
 */
function getModelDisplayName(modelData) {
    if (!modelData || !modelData.name) {
        return modelData?.model || "";
    }
    if (typeof modelData.name === "object") {
        return modelData.name.en_US || Object.values(modelData.name)[0] || modelData.model;
    }
    return String(modelData.name);
}

// Patching the CommandPalette for adding condition while using "!" command
patch(CommandPalette.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
    },

    // Access custom commands from the user
    async onKeyDown(ev) {
        if (ev.key === "Enter" && this.state.namespace === "!") {
            const searchValue = this.state.searchValue.trim();
            const firstWord = searchValue.split(/\s+/)[0].toLowerCase();

            if (firstWord === "open") {
                const regexSlash = /^Open.*\/.*$/i;
                const regexOfIn = /^Open\s+(.*?)\s+\b(?:of|in)\b\s+(.*)$/i;
                const regexSimple = /^Open\s+(.*)$/i;

                if (regexSlash.test(searchValue)) {
                    const parts = searchValue.split("/");
                    const modelName = parts[0].replace(/^Open\s*/i, "").trim();
                    const res = await this.orm.call("ir.model", "check_model", [modelName]);

                    if (res.length !== 0) {
                        this.model = res[0].model;
                        this.model_name = getModelDisplayName(res[0]);
                        const data = {
                            model: this.model,
                            record: parts[1].trim(),
                            regex: 1,
                        };
                        const recordIds = await this.orm.call("ir.model", "get_records", [data], {});
                        if (!Array.isArray(recordIds) || recordIds.length === 0) {
                            this.props.close();
                            this.dialog.add(AlertDialog, {
                                body: _t("No records found."),
                            });
                        } else if (recordIds.length === 1) {
                            this.action.doAction({
                                type: "ir.actions.act_window",
                                res_model: this.model,
                                views: [[false, "form"]],
                                target: "current",
                                res_id: recordIds[0],
                            });
                            this.props.close();
                        } else {
                            this.action.doAction({
                                name: this.model_name || "Records",
                                type: "ir.actions.act_window",
                                res_model: this.model,
                                domain: [["id", "in", recordIds]],
                                views: [[false, "list"], [false, "form"]],
                                view_mode: "list,form",
                                target: "current",
                            });
                            this.props.close();
                        }
                    } else {
                        this.props.close();
                        this.dialog.add(AlertDialog, {
                            body: _t("Model not found."),
                        });
                    }
                } else if (regexOfIn.test(searchValue)) {
                    const match = searchValue.match(regexOfIn);
                    const modelStr = match[1].trim();
                    const queryStr = match[2].trim();
                    const result = await this.orm.call("ir.model", "check_model", [modelStr], {});
                    if (result.length !== 0) {
                        this.model = result[0].model;
                        this.model_name = getModelDisplayName(result[0]);
                        await this._fields_check(this.model, queryStr);
                    } else {
                        // Fallback: in case the entire query is a model name containing "of" or "in" (e.g. "Point of Sale")
                        const fullModelStr = searchValue.replace(/^Open\s+/i, "").trim();
                        const fullResult = await this.orm.call("ir.model", "check_model", [fullModelStr], {});
                        if (fullResult.length !== 0) {
                            this.action.doAction({
                                name: getModelDisplayName(fullResult[0]),
                                type: "ir.actions.act_window",
                                res_model: fullResult[0].model,
                                views: [[false, "list"], [false, "form"]],
                                view_mode: "list,form",
                                target: "current",
                            });
                            this.props.close();
                        } else {
                            this.props.close();
                            this.dialog.add(AlertDialog, {
                                body: _t("Command not found."),
                            });
                        }
                    }
                } else if (regexSimple.test(searchValue)) {
                    const match = searchValue.match(regexSimple);
                    const modelStr = match[1].trim();
                    const res = await this.orm.call("ir.model", "check_model", [modelStr], {});
                    if (res.length !== 0) {
                        this.action.doAction({
                            name: getModelDisplayName(res[0]),
                            type: "ir.actions.act_window",
                            res_model: res[0].model,
                            views: [[false, "list"], [false, "form"]],
                            view_mode: "list,form",
                            target: "current",
                        });
                        this.props.close();
                    } else {
                        this.props.close();
                        this.dialog.add(AlertDialog, {
                            body: _t("Command not found."),
                        });
                    }
                } else {
                    this.props.close();
                    this.dialog.add(AlertDialog, {
                        body: _t("Command not found."),
                    });
                }
            } else if (firstWord === "create") {
                const regexCreate = /^Create\s+(.*)$/i;
                const match = searchValue.match(regexCreate);
                if (match) {
                    const modelStr = match[1].trim();
                    const res = await this.orm.call("ir.model", "check_model", [modelStr], {});
                    if (res.length !== 0) {
                        this.action.doAction({
                            type: "ir.actions.act_window",
                            res_model: res[0].model,
                            views: [[false, "form"]],
                            target: "current",
                        });
                        this.props.close();
                    } else {
                        this.props.close();
                        this.dialog.add(AlertDialog, {
                            body: _t("Model not found."),
                        });
                    }
                } else {
                    this.props.close();
                    this.dialog.add(AlertDialog, {
                        body: _t("Command not found."),
                    });
                }
            } else {
                this.props.close();
                this.dialog.add(AlertDialog, {
                    body: _t("Command not found."),
                });
            }
            return;
        }
        return super.onKeyDown(ev);
    },

    // Check fields for condition-based commands
    async _fields_check(model, queryStr) {
        const stringTokens = queryStr.split(/\s+/);
        const data = {
            model: model,
            field_string: stringTokens,
            regex: 2,
        };
        const res = await this.orm.call("ir.model", "check_fields_model", [data], {});
        if (res.length !== 0) {
            const delLen = res[0].del.length;
            if (queryStr.toLowerCase().startsWith(res[0].del.toLowerCase())) {
                data.field_string = queryStr.slice(delLen).trim();
            } else {
                const escapedDel = res[0].del.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
                data.field_string = queryStr.replace(new RegExp(`^${escapedDel}\\s*`, "i"), "").trim();
            }
            data.field = res[0].name;
            data.field_type = res[0].ttype;
            data.field_relation = res[0].relation;
            const recordIds = await this.orm.call("ir.model", "get_records", [data], {});
            if (!Array.isArray(recordIds) || recordIds.length === 0) {
                this.props.close();
                this.dialog.add(AlertDialog, {
                    body: _t("No records found."),
                });
            } else if (recordIds.length === 1) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: model,
                    views: [[false, "form"]],
                    target: "current",
                    res_id: recordIds[0],
                });
                this.props.close();
            } else {
                this.action.doAction({
                    name: this.model_name || "Records",
                    type: "ir.actions.act_window",
                    res_model: model,
                    domain: [["id", "in", recordIds]],
                    views: [[false, "list"], [false, "form"]],
                    view_mode: "list,form",
                    target: "current",
                });
                this.props.close();
            }
        } else {
            this.props.close();
            this.dialog.add(AlertDialog, {
                body: _t("Command not found."),
            });
        }
    },

    // Executing the command
    async executeCommand(command) {
        if (this.state.namespace === "!" && command?.name === "model_command_help") {
            return;
        }
        return super.executeCommand(...arguments);
    },
});
