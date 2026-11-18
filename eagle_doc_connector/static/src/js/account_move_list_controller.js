/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { AccountMoveListController } from "@account/views/account_move_list/account_move_list_controller";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { proxy, onWillStart } from "@odoo/owl";

/** Patches list controller to add "Upload to Eagle Doc" action. */
patch(AccountMoveListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.notificationService = useService("notification");
        this.orm = useService("orm");
        this.eagleDocState = proxy({ isAccountant: true });
        onWillStart(async () => {
            const hasInvoiceGroup = await user.hasGroup("account.group_account_invoice");
            const hasAccountGroup = await user.hasGroup("account.group_account_user");
            this.eagleDocState.isAccountant = hasInvoiceGroup || hasAccountGroup;
        });
    },

    /** Whether to show the upload button. */
    get showEagleDocButton() {
        const context = { ...this.env.searchModel?.context, ...this.props.context };
        const moveType = context.default_move_type || context.move_type;
        const isNotEntry = !moveType || moveType !== "entry";
        return isNotEntry && (this.eagleDocState ? this.eagleDocState.isAccountant : true);
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
            const moveType = this.props.context?.default_move_type || "in_invoice";
            const createdMoveIds = [];
            let failedCount = 0;
            this.notificationService.add(
                _t("Uploading %(count)s document(s) to Eagle Doc…", {
                    count: files.length,
                }),
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
                    const errorMsg = error.data?.message || error.message || _t("Failed to scan document");
                    this.notificationService.add(
                        `${file.name}: ${errorMsg}`,
                        { type: "danger" }
                    );
                }
            }
            if (!createdMoveIds.length) {
                return;
            }
            if (failedCount) {
                this.notificationService.add(
                    _t("%(uploaded)s document(s) uploaded, %(failed)s failed.", {
                        uploaded: createdMoveIds.length,
                        failed: failedCount,
                    }),
                    { type: "warning" }
                );
            } else {
                this.notificationService.add(
                    _t("%(count)s document(s) uploaded to Eagle Doc.", {
                        count: createdMoveIds.length,
                    }),
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
                    name: _t("Scanned via Eagle Doc"),
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
                resolve(uploadEvent.target.result.split(",")[1]);
            };
            reader.onerror = () => reject(new Error(_t("Failed to read %(name)s", { name: file.name })));
            reader.readAsDataURL(file);
        });
    },
});
