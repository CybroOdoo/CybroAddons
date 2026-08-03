/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileInput } from "@web/core/file_input/file_input";
import { download } from "@web/core/network/download";
import { isBinarySize, toBase64Length } from "@web/core/utils/binary";
import { _t } from "@web/core/l10n/translation";

import { Component } from "@odoo/owl";

export const MAX_FILENAME_SIZE_BYTES = 0xFF;
export const UPLOAD_ROUTE = "/media_repository/asset/upload_file";

export class LargeFileBinaryField extends Component {
    static template = "media_repository.LargeFileBinaryField";
    static components = { FileInput };
    static props = {
        ...standardFieldProps,
        fileNameField: { type: String, optional: true },
    };

    setup() {
        this.notification = useService("notification");
        this.uploadRoute = UPLOAD_ROUTE;
    }

    get fileName() {
        const { record, fileNameField, name } = this.props;
        let value = record.data[name];
        value = value && typeof value === "string" ? value : false;
        return (record.data[fileNameField] || value || "").slice(
            0,
            toBase64Length(MAX_FILENAME_SIZE_BYTES)
        );
    }

    get hasFile() {
        return Boolean(this.props.record.data[this.props.name]);
    }

    async onFileUploaded(data) {
        if (data.error) {
            this.notification.add(data.error, { type: "danger" });
            return;
        }
        await this.props.record.load();
    }

    async onFileDownload() {
        await download({
            data: {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                filename_field: this.fileName,
                filename: this.fileName || "",
                download: true,
                data: isBinarySize(this.props.record.data[this.props.name])
                    ? null
                    : this.props.record.data[this.props.name],
            },
            url: "/web/content",
        });
    }

    async onFileRemove() {
        const { fileNameField, record } = this.props;
        const changes = { [this.props.name]: false };
        if (fileNameField in record.fields) {
            changes[fileNameField] = false;
        }
        await record.update(changes);
    }
}

export const largeFileBinaryField = {
    component: LargeFileBinaryField,
    displayName: _t("Large File"),
    supportedTypes: ["binary"],
    extractProps: ({ attrs }) => ({
        fileNameField: attrs.filename,
    }),
};

registry.category("fields").add("media_large_file", largeFileBinaryField);
