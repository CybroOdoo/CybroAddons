import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { ImportAction } from "@base_import/import_action/import_action";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";

/** Message of an RPC error: the server's UserError text when there is one. */
function errorMessage(error, fallback) {
    if (error?.data?.message) {
        return error.data.message;
    }
    if (error?.message) {
        return error.message;
    }
    return typeof error === "string" ? error : fallback;
}

export class InstantImport extends ImportAction {
    static template = "instant_import.ImportAction";
    static components = { ...ImportAction.components, BlockUI };
    static path = "instant_import";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.blockUI = useService("ui");
        this.state.isTest = false;
    }

    async handleImport() {
        try {
            this.blockUI.block({ message: _t("Your records are being imported...") });
            const result = await this.orm.call(
                "custom.import.wizard",
                "copy_import",
                [this.model.id, this.resModel, this.model.columns],
                { options: this.model.importOptions }
            );
            if (result && result.record_count) {
                this.notification.add(
                    _t("%(count)s records successfully imported", { count: result.record_count }),
                    { type: "success" }
                );
                this.actionService.doAction({
                    type: "ir.actions.act_window",
                    res_model: this.resModel,
                    name: result.name,
                    views: [[false, "list"], [false, "kanban"], [false, "form"]],
                    target: "main",
                });
            }
        } catch (error) {
            this.notification.add(errorMessage(error, _t("Import failed. Please check your data.")), {
                type: "danger",
                sticky: true,
            });
        } finally {
            this.blockUI.unblock();
        }
    }

    async handleTest() {
        try {
            this.blockUI.block({ message: _t("Your records are being tested...") });
            const validationResult = await this.orm.call(
                "custom.import.wizard",
                "validate_columns",
                [this.model.id, this.resModel, this.model.columns],
                { options: this.model.importOptions }
            );
            if (validationResult && validationResult.is_valid) {
                this.notification.add(_t("Everything seems valid"), { type: "success" });
            } else {
                let message = validationResult.error_message || _t("Validation failed");
                if (!validationResult.error_message && validationResult.invalid_columns) {
                    message = _t("The following columns do not match Odoo fields: %(columns)s", {
                        columns: validationResult.invalid_columns.join(", "),
                    });
                }
                this.notification.add(message, { type: "danger", sticky: true });
            }
        } catch (error) {
            this.notification.add(
                errorMessage(error, _t("Validation failed. Please check your data.")),
                { type: "danger", sticky: true }
            );
        } finally {
            this.state.isTest = true;
            this.blockUI.unblock();
        }
    }
}

registry.category("actions").add("instant_import", InstantImport);
