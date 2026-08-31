/** @odoo-module **/
/**
 * Monkey-patches for Odoo 19 Website Builder bugs that cause crashes
 * when editing the BuildCraft homepage.
 *
 * Bug 1: MovePlugin.areArrowsHidden crashes with
 *   "Cannot read properties of null (reading 'children')"
 *   when a section is deleted, because overlayTarget.parentNode is null.
 *
 * Bug 2: WebsiteBuilderClientAction.resolveIframeLoaded crashes with
 *   "Cannot read properties of null (reading 'replaceChildren')"
 *   because iframefallback's documentElement can be null on certain
 *   page navigations (e.g. going to the project detail page in the builder).
 */
import { patch } from "@web/core/utils/patch";
import { MovePlugin } from "@html_builder/core/move_plugin";
import { WebsiteBuilderClientAction } from "@website/client_actions/website_preview/website_builder_action";

patch(MovePlugin.prototype, {
    areArrowsHidden() {
        if (!this.overlayTarget || !this.overlayTarget.parentNode) {
            return true;
        }
        return super.areArrowsHidden(...arguments);
    },
    getActiveOverlayButtons(target) {
        if (!target || !target.parentNode) {
            this.overlayTarget = null;
            return [];
        }
        return super.getActiveOverlayButtons(...arguments);
    },
});

patch(WebsiteBuilderClientAction.prototype, {
    async resolveIframeLoaded() {
        try {
            // Guard: if the iframe's documentElement is null (e.g. during
            // navigation to non-editable pages like /project/<id>), skip
            // the replaceChildren call to avoid a hard crash.
            const iframeDoc = this.iframefallback && this.iframefallback.contentDocument;
            if (!iframeDoc || !iframeDoc.documentElement) {
                return;
            }
            return await super.resolveIframeLoaded(...arguments);
        } catch (e) {
            // Silently swallow null-dereference errors from core builder
            // internals so the builder remains usable after navigation.
            if (e instanceof TypeError && e.message.includes("null")) {
                console.warn("[BuildCraft] resolveIframeLoaded guarded error:", e.message);
                return;
            }
            throw e;
        }
    },
});
