/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { _t } from '@web/core/l10n/translation';
import { BuilderAction } from "@html_builder/core/builder_action";
import { BaseOptionComponent } from "@html_builder/core/utils";


class DynamicLinkOption extends BaseOptionComponent {
    static template = "dynamic_link_snippet.DynamicLinkOption";
    static selector = "section";
    static title = _t("Dynamic Link");
    static groups = ["website.group_website_designer"];
}
export class DynamicLinkPlugin extends Plugin{
    static id="DynamicLinkOption";
    resources = {
        builder_options: DynamicLinkOption,
        builder_actions: {
            DynamicLinkAction
        }
    }
}
export class DynamicLinkAction extends BuilderAction {
    static id = "linkid";
    static dependencies = ["DynamicLinkOption"];

    getValue({ editingElement }) {
        return editingElement.dataset.linkid || "";
    }

    async apply({ editingElement: fieldEl, value }) {
        fieldEl.dataset.linkid = value;
        const frameWrapper = fieldEl.querySelector(".iframes");
        console.log(frameWrapper)
        if (frameWrapper) {
            frameWrapper.innerHTML = "";
            if (value) {
                const iframeHTML = `
                    <iframe
                        id="url_id"
                        src="${value}"
                        width="100%"
                        height="100%"
                        style="border:none;"
                    ></iframe>
                `;
                frameWrapper.insertAdjacentHTML("afterbegin", iframeHTML);
            }
        }
    }
}

registry.category("website-plugins").add(DynamicLinkPlugin.id, DynamicLinkPlugin);
