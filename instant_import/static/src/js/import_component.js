/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ImportAction } from "@base_import/import_action/import_action";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";

export class InstantImport extends ImportAction {
    static template = "instant_import.ImportAction";
    static components = { ...ImportAction.components, BlockUI };

    setup() {
        super.setup();
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService("notification");
        this.blockUI = useService("ui");
    }

    async handleImport(isTest = true) {
        try {
            this.blockUI.block({
                message: "Your records are being imported...",
            });

            const result = await this.orm.call(
                "custom.import.wizard",
                "copy_import",
                [this.model.id, this.props.action.params.model, this.model.columns],
                {}
            );

            if (result && result.record_count) {
                this.notification.add(`${result.record_count} Records successfully imported`, {
                    type: "success",
                });

                // Redirect to the relevant view after successful import
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: this.props.action.params.model,
                    name: result.name,
                    views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
                    target: 'main',
                });
            }

        } catch (error) {
            console.error("Import error:", error);

            // Extract the actual error message from the error object
            let errorMessage = "Import failed. Please check your data.";

            if (error && error.data && error.data.message) {
                // This handles UserError messages from Python
                errorMessage = error.data.message;
            } else if (error && error.message) {
                // This handles other types of error messages
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }

            this.notification.add(errorMessage, {
                type: "danger",
                sticky: true, // Keep the error message visible longer
            });
        } finally {
            this.blockUI.unblock();
        }
    }

    async handleTest() {
        try {
            this.blockUI.block({
                message: "Your records are being tested...",
            });

            const validationResult = await this.orm.call(
                "custom.import.wizard",
                "validate_columns",
                [this.model.id, this.props.action.params.model, this.model.columns],
                {}
            );

            if (validationResult && validationResult.is_valid) {
                this.notification.add(`Everything seems valid`, {
                    type: "success",
                });
            } else {
                // Handle different types of validation errors
                let errorMessage = "Validation failed";

                if (validationResult.error_type === 'missing_required_fields') {
                    errorMessage = validationResult.error_message ||
                        `Required fields missing: ${validationResult.missing_required_fields.join(", ")}. Please add these columns to your Excel file.`;
                } else if (validationResult.error_type === 'invalid_columns') {
                    errorMessage = `The following columns do not match Odoo fields: ${validationResult.invalid_columns.join(", ")}`;
                } else if (validationResult.error_message) {
                    errorMessage = validationResult.error_message;
                } else if (validationResult.invalid_columns) {
                    errorMessage = `The following columns do not match Odoo fields: ${validationResult.invalid_columns.join(", ")}`;
                }

                this.notification.add(errorMessage, {
                    type: "danger",
                    sticky: true, // Keep the error message visible longer
                });
            }

        } catch (error) {
            console.error("Error during column validation:", error);

            // Extract the actual error message from the error object
            let errorMessage = "Validation failed. Please check your data.";

            if (error && error.data && error.data.message) {
                errorMessage = error.data.message;
            } else if (error && error.message) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }

            this.notification.add(errorMessage, {
                type: "danger",
                sticky: true,
            });
        } finally {
            this.blockUI.unblock();
        }
    }
}

registry.category("actions").add("instant_import", InstantImport);