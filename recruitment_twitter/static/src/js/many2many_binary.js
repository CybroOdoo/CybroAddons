/** @odoo-module **/
import { Many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field"
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Many2ManyBinaryField.prototype, {
async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: _t("Uploading error"),
                    type: "danger",
                });
            }
            if (this.props.record.resModel === "hr.job" && file.mimetype !== "image/png"){
            return this.notification.add(file.error, {
                    title: _t("Uploading error File is not an image"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
        }
    }});