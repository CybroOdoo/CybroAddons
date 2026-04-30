/** @odoo-module **/

import { BuilderAction } from "@html_builder/core/builder_action";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";

const OPT_SEQ = 5;

// ── Products Carousel: Add / Remove Card ─────────────────────────────────────

class AddProductCardAction extends BuilderAction {
    static id = "addProductCard";
    apply({ editingElement }) {
        const section = editingElement.closest(".ipc-section") || editingElement;
        const reel = section.querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (!cards.length) return;
        const copy = cards[cards.length - 1].cloneNode(true);
        reel.appendChild(copy);
    }
}

class RemoveProductCardAction extends BuilderAction {
    static id = "removeProductCard";
    apply({ editingElement }) {
        const section = editingElement.closest(".ipc-section") || editingElement;
        const reel = section.querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (cards.length <= 1) return;
        cards[cards.length - 1].remove();
    }
}

// ── Brand Logo Strip: Add / Remove Logo ──────────────────────────────────────

class AddBrandLogoAction extends BuilderAction {
    static id = "addBrandLogo";
    apply({ editingElement }) {
        const section = editingElement.closest(".interioro-brand-strip") || editingElement;
        const track = section.querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (!logos.length) return;
        track.appendChild(logos[logos.length - 1].cloneNode(true));
    }
}

class RemoveBrandLogoAction extends BuilderAction {
    static id = "removeBrandLogo";
    apply({ editingElement }) {
        const section = editingElement.closest(".interioro-brand-strip") || editingElement;
        const track = section.querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (logos.length <= 1) return;
        logos[logos.length - 1].remove();
    }
}

class InterioroSnippetPlugin extends Plugin {
    static id = "interioroSnippetPlugin";
    resources = {
        builder_options: [
            withSequence(OPT_SEQ, {
                template: "theme_interioro.productsCarouselOption",
                selector: ".ipc-section",
            }),
            withSequence(OPT_SEQ, {
                template: "theme_interioro.brandStripOption",
                selector: ".interioro-brand-strip",
            }),
        ],
        builder_actions: {
            AddProductCardAction,
            RemoveProductCardAction,
            AddBrandLogoAction,
            RemoveBrandLogoAction,
        },
    };
}

registry.category("website-plugins").add(InterioroSnippetPlugin.id, InterioroSnippetPlugin);
