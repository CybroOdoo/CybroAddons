/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { renderToElement } from "@web/core/utils/render";
import { WebsiteBuilderClientAction } from "@website/client_actions/website_preview/website_builder_action";

// Patch the Website builder preview client action to ensure the welcome message logic
// remains compatible with Odoo 19 API (websiteContent.el, state.isEditing)
patch(WebsiteBuilderClientAction.prototype, {
    addWelcomeMessage() {
        // Call original behavior first (safest for compatibility)
        if (this._super) {
            this._super.apply(this, arguments);
        }
        // Custom safeguard: ensure message when homepage is empty for restricted editors
        if (this.websiteService.isRestrictedEditor && !this.state.isEditing) {
            const wrap = this.websiteContent?.el?.contentDocument?.querySelector('#wrapwrap.homepage #wrap');
            if (wrap && !wrap.innerHTML.trim()) {
                const msg = renderToElement('website.homepage_editor_welcome_message');
                msg.classList.add('o_homepage_editor_welcome_message', 'h-100');
                wrap.replaceChildren(msg);
            }
        }
    },
});
