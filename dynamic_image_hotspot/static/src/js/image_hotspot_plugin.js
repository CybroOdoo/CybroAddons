/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { BaseOptionComponent } from "@html_builder/core/base_option_component";
import { BuilderAction } from "@html_builder/core/builder_action";
import { useDomState } from "@html_builder/core/utils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Return the `.popup-product` anchor that immediately follows `imgEl`, or null.
 * @param {HTMLImageElement} imgEl
 * @returns {HTMLAnchorElement|null}
 */
function getAnchor(imgEl) {
    const next = imgEl.nextElementSibling;
    return next && next.classList.contains("popup-product") ? next : null;
}

/**
 * Create and insert a fresh `.popup-product` anchor after `imgEl`,
 * seeding position and href from the image's data-attributes.
 * @param {HTMLImageElement} imgEl
 * @returns {HTMLAnchorElement}
 */
function createAnchor(imgEl) {
    const anchor = imgEl.ownerDocument.createElement("a");
    anchor.className = "popup-product";
    anchor.style.left = `${imgEl.dataset.hotspotX || 50}%`;
    anchor.style.top  = `${imgEl.dataset.hotspotY  || 50}%`;
    const pid = imgEl.dataset.hotspotProductId;
    if (pid) {
        anchor.setAttribute("href", `/shop/${pid}`);
    }
    imgEl.after(anchor);
    return anchor;
}

// ---------------------------------------------------------------------------
// OWL Component — builder options panel
// ---------------------------------------------------------------------------

export class ImageHotspotOption extends BaseOptionComponent {
    static id = "image_hotspot_option";
    static template = "dynamic_image_hotspot.ImageHotspotOption";

    setup() {
        super.setup();
        this.state = useDomState((editingElement) => ({
            isHotspotOn: editingElement?.dataset?.hotspot === "on",
        }));
    }
}

registry.category("website-options").add(ImageHotspotOption.id, ImageHotspotOption);

// ---------------------------------------------------------------------------
// Builder Actions — DOM mutations driven by sidebar interactions
// ---------------------------------------------------------------------------

/** Toggle the hotspot on/off. */
export class ImageHotspotToggleAction extends BuilderAction {
    static id = "imageHotspotToggle";

    getValue({ editingElement: imgEl }) {
        return imgEl.dataset.hotspot === "on" ? "on" : "off";
    }

    isApplied({ editingElement: imgEl, value }) {
        const active = imgEl.dataset.hotspot === "on";
        return value !== undefined ? (value === "on" ? active : !active) : active;
    }

    apply({ editingElement: imgEl, value }) {
        if (value === "on") {
            imgEl.dataset.hotspot = "on";
            imgEl.parentElement.style.position = "relative";
            if (!getAnchor(imgEl)) {
                createAnchor(imgEl);
            }
        } else {
            // Remove all stored hotspot data and live preview
            delete imgEl.dataset.hotspot;
            delete imgEl.dataset.hotspotX;
            delete imgEl.dataset.hotspotY;
            delete imgEl.dataset.hotspotProductId;
            getAnchor(imgEl)?.remove();
        }
    }

    clean({ editingElement: imgEl }) {
        delete imgEl.dataset.hotspot;
        delete imgEl.dataset.hotspotX;
        delete imgEl.dataset.hotspotY;
        delete imgEl.dataset.hotspotProductId;
        getAnchor(imgEl)?.remove();
    }
}

/** Adjust the horizontal (left %) position. */
export class ImageHotspotHorizontalAction extends BuilderAction {
    static id = "imageHotspotHorizontal";

    getValue({ editingElement: imgEl }) {
        return parseFloat(imgEl.dataset.hotspotX) || 50;
    }

    apply({ editingElement: imgEl, value }) {
        const val = parseFloat(value) || 50;
        imgEl.dataset.hotspotX = val;
        let anchor = getAnchor(imgEl);
        if (!anchor && imgEl.dataset.hotspot === "on") {
            anchor = createAnchor(imgEl);
        }
        if (anchor) anchor.style.left = `${val}%`;
    }

    clean({ editingElement: imgEl }) {
        delete imgEl.dataset.hotspotX;
    }
}

/** Adjust the vertical (top %) position. */
export class ImageHotspotVerticalAction extends BuilderAction {
    static id = "imageHotspotVertical";

    getValue({ editingElement: imgEl }) {
        return parseFloat(imgEl.dataset.hotspotY) || 50;
    }

    apply({ editingElement: imgEl, value }) {
        const val = parseFloat(value) || 50;
        imgEl.dataset.hotspotY = val;
        let anchor = getAnchor(imgEl);
        if (!anchor && imgEl.dataset.hotspot === "on") {
            anchor = createAnchor(imgEl);
        }
        if (anchor) anchor.style.top = `${val}%`;
    }

    clean({ editingElement: imgEl }) {
        delete imgEl.dataset.hotspotY;
    }
}

/** Link a product template to the hotspot anchor. */
export class ImageHotspotProductAction extends BuilderAction {
    static id = "imageHotspotProduct";

    getValue({ editingElement: imgEl }) {
        const pid = imgEl.dataset.hotspotProductId;
        return pid ? JSON.stringify({ id: parseInt(pid, 10) }) : null;
    }

    apply({ editingElement: imgEl, value }) {
        const parsed = typeof value === "string" ? JSON.parse(value) : value;
        const id = parsed?.id;
        let anchor = getAnchor(imgEl);
        if (!anchor && imgEl.dataset.hotspot === "on") {
            anchor = createAnchor(imgEl);
        }

        if (id) {
            imgEl.dataset.hotspotProductId = id;
            if (anchor) anchor.setAttribute("href", `/shop/${id}`);
        } else {
            delete imgEl.dataset.hotspotProductId;
            if (anchor) anchor.removeAttribute("href");
        }
    }

    clean({ editingElement: imgEl }) {
        delete imgEl.dataset.hotspotProductId;
        const anchor = getAnchor(imgEl);
        if (anchor) anchor.removeAttribute("href");
    }
}

// ---------------------------------------------------------------------------
// Plugin — registers everything into the html_builder / website-plugins
// ---------------------------------------------------------------------------

export class ImageHotspotPlugin extends Plugin {
    static id = "imageHotspot";

    resources = {
        builder_actions: {
            ImageHotspotToggleAction,
            ImageHotspotHorizontalAction,
            ImageHotspotVerticalAction,
            ImageHotspotProductAction,
        },
        // Re-inject preview anchors when editor loads / history steps apply
        normalize_processors: this.normalize.bind(this),
        // Strip preview anchors before the HTML is persisted to DB
        clean_for_save_processors: (root) => this.cleanForSave(root),
    };

    normalize(node) {
        if (node?.querySelectorAll) {
            for (const imgEl of node.querySelectorAll("img[data-hotspot='on']")) {
                imgEl.parentElement.style.position = "relative";
                if (!getAnchor(imgEl)) {
                    createAnchor(imgEl);
                }
            }
        }
        return node;
    }

    cleanForSave(root) {
        if (root?.querySelectorAll) {
            for (const anchor of root.querySelectorAll("a.popup-product")) {
                anchor.remove();
            }
        }
        return root;
    }
}

registry.category("website-plugins").add(ImageHotspotPlugin.id, ImageHotspotPlugin);
