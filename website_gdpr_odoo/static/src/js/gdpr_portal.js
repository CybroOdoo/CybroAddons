import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Personal data page: send a download request at once, and a delete request
 * after the confirmation of the customer
 */
export class GdprPortal extends Interaction {
    static selector = ".o_gdpr_portal";
    dynamicContent = {
        ".o_gdpr_download": {
            "t-on-click": (ev) => this.sendRequest(ev.currentTarget.dataset.templateId, "download"),
        },
        ".o_gdpr_delete": {
            "t-on-click": (ev) => {
                this.deleteTemplateId = ev.currentTarget.dataset.templateId;
            },
        },
        ".o_gdpr_confirm_delete": {
            "t-on-click": () => this.sendRequest(this.deleteTemplateId, "delete"),
        },
    };

    async sendRequest(templateId, reqType) {
        const result = await this.waitFor(
            rpc("/gdpr_management/confirm", { template_id: templateId, req_type: reqType })
        );
        window.location.href = `/gdpr_management/submit?status=${result.status}`;
    }
}

registry.category("public.interactions").add("website_gdpr_odoo.gdpr_portal", GdprPortal);
