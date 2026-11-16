/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {
    Many2ManyBinaryField,
    many2ManyBinaryField,
} from "@web/views/fields/many2many_binary/many2many_binary_field";
import { Many2XBinary } from "@web/views/fields/many2x_binary/many2x_binary";
import { useProps, t } from "@odoo/owl";

export class DocusignMany2XBinary extends Many2XBinary {
    static template = "docusign_odoo_connector.DocusignMany2XBinary";
    props = useProps({
        ...standardFieldProps,
        onFileUploaded: t.function(),
        onFileRemove: t.function(),
        files: t.array(),
        acceptedFileExtensions: t.string().optional(),
        className: t.string().optional(),
        multiUpload: t.boolean().optional(false),
        numberOfFiles: t.number().optional(),
        onConfigureDocument: t.function().optional(),
    });

    get isWizardApplicable() {
        if (this.props.record.resModel === "docusign.document.request.line") {
            return true;
        }
        if (this.props.record.resModel === "docusign.document.request") {
            return this.props.record.data.selection_type === "mandatory";
        }
        return false;
    }

    onCardClick(fileId) {
        if (this.isWizardApplicable && !this.props.readonly) {
            this.props.onConfigureDocument?.(fileId);
        }
    }
}

export class DocusignMany2ManyBinaryField extends Many2ManyBinaryField {
    static template = "docusign_odoo_connector.DocusignMany2ManyBinaryField";
    static components = {
        Many2XBinary: DocusignMany2XBinary,
    };

    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    isWizardApplicable() {
        if (this.props.record.resModel === "docusign.document.request.line") {
            return true;
        }
        if (this.props.record.resModel === "docusign.document.request") {
            return this.props.record.data.selection_type === "mandatory";
        }
        return false;
    }

    getPartnerIds() {
        if (this.props.record.resModel === "docusign.document.request.line") {
            const partner = this.props.record.data.partner_id;
            if (!partner) return [];
            if (Array.isArray(partner) && partner.length > 0) return [partner[0]];
            if (typeof partner === "number") return [partner];
            if (partner && partner.id) return [partner.id];
            if (partner && partner.resId) return [partner.resId];
            return [];
        }

        const partnerData = this.props.record.data.partner_ids;
        if (!partnerData) return [];
        if (partnerData.records && Array.isArray(partnerData.records)) {
            return partnerData.records.map((r) => r.resId).filter(Boolean);
        } else if (Array.isArray(partnerData)) {
            const ids = [];
            for (const item of partnerData) {
                if (typeof item === "number") ids.push(item);
                else if (item && item.id) ids.push(item.id);
                else if (Array.isArray(item) && item[0] === 4) ids.push(item[1]);
                else if (Array.isArray(item) && item[0] === 6 && Array.isArray(item[2])) ids.push(...item[2]);
            }
            return ids;
        }
        return [];
    }

    getRequestId() {
        if (this.props.record.resModel === "docusign.document.request") {
            return this.props.record.resId || false;
        }
        if (this.props.record.resModel === "docusign.document.request.line") {
            const req = this.props.record.data.request_id;
            if (Array.isArray(req) && req.length > 0) return req[0];
            if (typeof req === "number") return req;
            if (req && req.id) return req.id;
            if (this.props.record.model?.root?.resModel === "docusign.document.request") {
                return this.props.record.model.root.resId || false;
            }
        }
        return false;
    }

    async onFileUploaded(files) {
        const validFileIds = [];
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: _t("Uploading error"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
            validFileIds.push(file.id);
        }

        if (this.isWizardApplicable() && validFileIds.length > 0) {
            const partnerIds = this.getPartnerIds();
            if (partnerIds.length === 0) {
                this.notification.add(
                    _t("Please select a Customer before configuring document fields."),
                    { type: "warning" }
                );
                return;
            }

            if (this.props.record.model?.root?.dirty) {
                try {
                    await this.props.record.model.root.save();
                } catch (e) {
                    console.warn("Could not save root record before opening wizard:", e);
                }
            } else if (this.props.record.dirty) {
                try {
                    await this.props.record.save();
                } catch (e) {
                    console.warn("Could not save record before opening wizard:", e);
                }
            }
            await this.openDocumentConfigWizard(validFileIds);
        }
    }

    async openDocumentConfigWizard(fileIds) {
        try {
            const partnerIds = this.getPartnerIds();
            const action = await this.orm.call(
                "docusign.document.request",
                "action_open_document_wizard",
                [],
                {
                    attachment_ids: fileIds,
                    request_id: this.getRequestId(),
                    partner_ids: partnerIds,
                }
            );
            if (action) {
                if (action.type === "ir.actions.act_window" && !action.views) {
                    action.views = [[action.view_id || false, "form"]];
                }
                await this.action.doAction(action, {
                    onClose: async () => {
                        await this.props.record.load();
                    },
                });
            }
        } catch (error) {
            console.error("Error opening document configuration wizard:", error);
            this.notification.add(
                _t("Could not open field configuration window: %s", error.data?.message || error.message || error),
                { type: "danger" }
            );
        }
    }

    async onConfigureDocument(fileId) {
        if (!this.isWizardApplicable()) {
            return;
        }
        const partnerIds = this.getPartnerIds();
        if (partnerIds.length === 0) {
            this.notification.add(
                _t("Please select a Customer before configuring document fields."),
                { type: "warning" }
            );
            return;
        }

        if (this.props.record.model?.root?.dirty) {
            try {
                await this.props.record.model.root.save();
            } catch (e) {
                console.warn("Could not save root record before opening wizard:", e);
            }
        } else if (this.props.record.dirty) {
            try {
                await this.props.record.save();
            } catch (e) {
                console.warn("Could not save record before opening wizard:", e);
            }
        }
        await this.openDocumentConfigWizard([fileId]);
    }
}

export const docusignMany2ManyBinaryField = {
    ...many2ManyBinaryField,
    component: DocusignMany2ManyBinaryField,
    relatedFields: [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
        { name: "docusign_tabs", type: "text" },
    ],
};

registry.category("fields").add("docusign_many2many_binary", docusignMany2ManyBinaryField);
