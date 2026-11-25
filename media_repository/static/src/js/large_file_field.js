/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { download } from "@web/core/network/download";
import { isBinarySize, toBase64Length } from "@web/core/utils/binary";
import { humanNumber } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";

import { Component, useRef, useState } from "@odoo/owl";

export const MAX_FILENAME_SIZE_BYTES = 0xFF;
export const UPLOAD_ROUTE = "/media_repository/asset/upload_file";
export const MAX_MEDIA_FILE_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024; // 2 GB

export class LargeFileBinaryField extends Component {
    static template = "media_repository.LargeFileBinaryField";
    static props = {
        ...standardFieldProps,
        fileNameField: { type: String, optional: true },
    };

    setup() {
        this.notification = useService("notification");
        this.http = useService("http");
        this.fileInputRef = useRef("fileInput");
        this.state = useState({
            isUploading: false,
        });
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

    onUploadBtnClick() {
        if (this.fileInputRef.el) {
            this.fileInputRef.el.click();
        }
    }

    async onFileInputChange() {
        const input = this.fileInputRef.el;
        if (!input || !input.files || !input.files.length) {
            return;
        }
        const file = input.files[0];
        if (file.size > MAX_MEDIA_FILE_UPLOAD_SIZE) {
            this.notification.add(
                _t(
                    "The selected file (%sB) is over the maximum allowed file size (%sB).",
                    humanNumber(file.size),
                    humanNumber(MAX_MEDIA_FILE_UPLOAD_SIZE)
                ),
                { type: "danger" }
            );
            input.value = null;
            return;
        }

        this.state.isUploading = true;
        try {
            const formData = new FormData();
            formData.append("csrf_token", odoo.csrf_token);
            formData.append("model", this.props.record.resModel);
            formData.append("id", this.props.record.resId);
            formData.append("ufile", file);

            const responseText = await this.http.post(this.uploadRoute, formData, "text");
            const data = JSON.parse(responseText);
            if (data.error) {
                this.notification.add(data.error, { type: "danger" });
            } else {
                await this.props.record.load();
            }
        } catch (err) {
            this.notification.add(
                _t("File upload failed: %s", err.message || err),
                { type: "danger" }
            );
        } finally {
            this.state.isUploading = false;
            if (this.fileInputRef.el) {
                this.fileInputRef.el.value = null;
            }
        }
    }

    async onFileDownload() {
        await download({
            data: {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                filename_field: this.props.fileNameField,
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
