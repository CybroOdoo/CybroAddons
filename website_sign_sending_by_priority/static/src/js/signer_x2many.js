/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { SignerX2Many } from "@sign/fields/signer_x2many";
//Extended SignerX2Many widget of the field signer_ids and created new widget,
//because we cant add the field to the existing widget
export class SignerX2ManyWithPriority extends SignerX2Many {
    static template = "website_sign_sending_by_priority.SignerX2ManyWithPriority";
    static components = {
        ...SignerX2Many.components,
    };

    get priorityFieldInfo() {
        return {
            name: "priority",
            additionalProps: {
                readonly: false,
            },
        };
    }
}

const signerX2ManyWithPriority = {
    component: SignerX2ManyWithPriority,
    displayName: _t("Signer One 2 Many with Priority"),
    additionalClasses: ["o_required_modifier"],
    supportedTypes: ["one2many"],
    relatedFields: () => {
        return [
            { name: "role_id", type: "many2one", relation: "sign.item.role", readonly: false },
            { name: "partner_id", type: "many2one", relation: "res.partner", readonly: false },
            { name: "priority", type: "integer", readonly: false },
            { name: "mail_sent_order", type: "integer", readonly: false },
        ];
    },
    fieldDependencies: [{ name: "set_sign_order", type: "boolean" }],
};

registry.category("fields").add("signer_x2many_with_priority", signerX2ManyWithPriority);
