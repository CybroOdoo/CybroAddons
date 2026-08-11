/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { AccountMoveListController } from "@account/views/account_move_list/account_move_list_controller";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { useState, onWillStart } from "@odoo/owl";

/** Patches list controller to add "Upload to Eagle Doc" action. */
patch(AccountMoveListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.notificationService = useService("notification");
        this.orm = useService("orm");
        this.eagleDocState = useState({ isAccountant: false });
        onWillStart(async () => {
            this.eagleDocState.isAccountant = await user.hasGroup("account.group_account_user");
        });
    },

    /** Whether to show the upload button. */
    get showEagleDocButton() {
        const moveType = this.props.context?.default_move_type;
        return ["out_invoice", "in_invoice"].includes(moveType) && this.eagleDocState.isAccountant;
    },

    /** Uploads selected files to Eagle Doc. */
    async actionUploadEagleDoc() {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*,application/pdf";
        input.multiple = true;
        input.onchange = async (ev) => {
            const files = Array.from(ev.target.files || []);
            if (!files.length) {
                return;
            }
            const moveType = this.props.context?.default_move_type || 'in_invoice';
            const createdMoveIds = [];
            let failedCount = 0;
            this.notificationService.add(
                `Uploading ${files.length} document(s) to Eagle Doc…`,
                { type: "info" }
            );
            for (const file of files) {
                try {
                    const base64Data = await this._readFileAsBase64(file);
                    const result = await this.orm.call(
                        "account.move",
                        "action_scan_via_eagle_doc",
                        [],
                        {
                            filename: file.name,
                            file_data: base64Data,
                            move_type: moveType,
                        }
                    );
                    if (result && result.res_id) {
                        createdMoveIds.push(result.res_id);
                    }
                } catch (error) {
                    failedCount += 1;
                    this.notificationService.add(
                        `${file.name}: ${error.message || "Failed to scan document"}`,
                        { type: "danger" }
                    );
                }
            }
            if (!createdMoveIds.length) {
                return;
            }
            if (failedCount) {
                this.notificationService.add(
                    `${createdMoveIds.length} document(s) uploaded, ${failedCount} failed.`,
                    { type: "warning" }
                );
            } else {
                this.notificationService.add(
                    `${createdMoveIds.length} document(s) uploaded to Eagle Doc.`,
                    { type: "success" }
                );
            }
            if (createdMoveIds.length === 1) {
                this.actionService.doAction({
                    type: "ir.actions.act_window",
                    res_model: "account.move",
                    view_mode: "form",
                    views: [[false, "form"]],
                    res_id: createdMoveIds[0],
                    target: "current",
                });
            } else {
                this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: "Scanned via Eagle Doc",
                    res_model: "account.move",
                    view_mode: "list,form",
                    views: [[false, "list"], [false, "form"]],
                    domain: [["id", "in", createdMoveIds]],
                    target: "current",
                });
            }
        };
        input.click();
    },

    _readFileAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (uploadEvent) => {
                resolve(uploadEvent.target.result.split(',')[1]);
            };
            reader.onerror = () => reject(new Error(`Failed to read ${file.name}`));
            reader.readAsDataURL(file);
        });
    }
});
