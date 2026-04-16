/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileInput } from "@web/core/file_input/file_input";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class Many2ManyAttachmentPreview extends Component {
    static template = "many2many_attachment_preview.Many2ManyAttachmentPreview";
    static components = { FileInput };
    static props = {
        ...standardFieldProps,
        acceptedFileExtensions: { type: String, optional: true },
        className: { type: String, optional: true },
        numberOfFiles: { type: Number, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.operations = useX2ManyCrud(() => this.props.record.data[this.props.name], true);
    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((r) => ({
            ...r.data,
            id: r.resId,
        }));
    }

    getUrl(id) {
        return `/web/content/${id}`;
    }

    getExtension(file) {
        return file.name.replace(/^.*\./, "");
    }

    isImage(file) {
        return file.mimetype?.startsWith("image/");
    }

    onFileClick(file, ev) {
        ev.preventDefault();
        ev.stopPropagation();

        this.dialog.add(FilePreviewDialog, {
            file: file,
        });
    }

    async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                this.notification.add(file.error, { title: "Upload Error", type: "danger" });
                return;
            }
            await this.operations.saveRecord([file.id]);
        }
    }

    async onFileRemove(deleteId) {
        const record = this.props.record.data[this.props.name].records.find(
            (r) => r.resId === deleteId
        );
        this.operations.removeRecord(record);
    }
}

class FilePreviewDialog extends Component {
    static template = "many2many_attachment_preview.FilePreviewDialog";
    static components = { Dialog };
    static props = {
        file: Object,
        close: Function,
    };

    getUrl(id) {
        return `/web/content/${id}`;
    }

    isImage(file) {
        return file.mimetype?.startsWith("image/");
    }

    isPDF(file) {
        return file.mimetype === "application/pdf";
    }

    isPreviewable(file) {
        return this.isImage(file) || this.isPDF(file);
    }

    downloadFile() {
        window.location.href = `/web/content/${this.props.file.id}?download=true`;
    }
}

export const many2ManyAttachmentPreview = {
    component: Many2ManyAttachmentPreview,
    supportedOptions: [
        {
            label: "Accepted file extensions",
            name: "accepted_file_extensions",
            type: "string",
        },
        {
            label: "Number of files",
            name: "number_of_files",
            type: "integer",
        },
    ],
    supportedTypes: ["many2many"],
    relatedFields: [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
    ],
    extractProps: ({ attrs, options }) => ({
        acceptedFileExtensions: options.accepted_file_extensions,
        className: attrs.class,
        numberOfFiles: options.number_of_files,
    }),
};

registry.category("fields").add("many2many_attachment_preview", many2ManyAttachmentPreview);