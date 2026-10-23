/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

patch(ListController.prototype, {
    /**
     * Handle the click event for uploading documents to selected records.
     */
    async _uploadMultiDocumentOnClickAttachment() {
        const selectedRecords = await this.model.root.getResIds(true);
        if (!selectedRecords || !selectedRecords.length) {
            this.dialogService.add(AlertDialog, {
                title: _t("Notice"),
                body: _t("Please select at least one record."),
                confirmLabel: _t("Ok"),
            });
            return;
        }

        const uploadFileInput = document.createElement("input");
        uploadFileInput.setAttribute("type", "file");
        uploadFileInput.setAttribute("multiple", "multiple");
        uploadFileInput.addEventListener("change", async (e) => {
            const files = Array.from(e.target.files || []);
            if (!files.length) {
                return;
            }

            const results = await Promise.allSettled(
                files.map(async (file) => {
                    const dataurl = await readFileAsDataURL(file);
                    return this.orm.call(
                        "upload.multi.documents",
                        "document_file_create",
                        [dataurl, file.name, selectedRecords, this.props.resModel]
                    );
                })
            );
            const failedNames = files
                .filter((file, index) => results[index].status === "rejected")
                .map((file) => file.name);

            if (failedNames.length < files.length) {
                // At least one file was attached: refresh the list.
                await this.model.load();
            }
            if (failedNames.length) {
                this.dialogService.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t(
                        "Some documents could not be uploaded (check that you have write access on the selected records): %(files)s",
                        { files: failedNames.join(", ") }
                    ),
                    confirmLabel: _t("Ok"),
                });
            } else {
                this.dialogService.add(AlertDialog, {
                    title: _t("Success"),
                    body: _t("Documents uploaded successfully."),
                    confirmLabel: _t("Ok"),
                });
            }
        });
        uploadFileInput.click();
    },
});
