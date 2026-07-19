/** @odoo-module **/

import { Component } from "@odoo/owl";

// ─── Lightbox Component ───────────────────────────────────────────────────────

class AiImageLightbox extends Component {
    static template = "smart_product_image_generator.ImageLightbox";
    static props = {
        imageUrl: { type: String },
        imageName: { type: String, optional: true },
        provider: { type: String, optional: true },
        style: { type: String, optional: true },
        onUse: { type: Function },
        onClose: { type: Function },
    };

    closeLightbox() {
        this.props.onClose();
    }

    useImage() {
        this.props.onUse();
        this.props.onClose();
    }

    downloadImage() {
        const link = document.createElement("a");
        link.href = this.props.imageUrl;
        link.download = this.props.imageName || "ai_generated.png";
        link.click();
    }
}

// ─── Standalone lightbox using native DOM ─────────────────────────────────────

let _lightboxEl = null;

function openLightbox(imageUrl, meta, onUse) {
    if (_lightboxEl) {
        _lightboxEl.remove();
        _lightboxEl = null;
    }

    _lightboxEl = document.createElement("div");
    _lightboxEl.className = "o_ai_lightbox_overlay";
    _lightboxEl.innerHTML = `
        <div class="o_ai_lightbox_dialog">
            <div class="o_ai_lightbox_header">
                <span class="o_ai_lightbox_title">
                    ${meta.provider ? `<strong>Provider:</strong> ${meta.provider}` : ""}
                    ${meta.style ? ` | <strong>Style:</strong> ${meta.style}` : ""}
                </span>
                <button class="btn-close js-close" aria-label="Close"></button>
            </div>
            <div class="o_ai_lightbox_body">
                <img src="${imageUrl}" class="o_ai_lightbox_img" alt="AI Generated Image"/>
            </div>
            <div class="o_ai_lightbox_footer">
                <button class="btn btn-primary js-use">&#10003; Use This Image</button>
                <button class="btn btn-secondary js-download">&#8595; Download</button>
                <button class="btn btn-secondary js-close">Cancel</button>
            </div>
        </div>
    `;

    const close = () => {
        if (_lightboxEl) {
            _lightboxEl.remove();
            _lightboxEl = null;
        }
    };

    _lightboxEl.querySelectorAll(".js-close").forEach((btn) => btn.addEventListener("click", close));
    _lightboxEl.addEventListener("click", (e) => { if (e.target === _lightboxEl) close(); });

    _lightboxEl.querySelector(".js-use").addEventListener("click", () => {
        onUse();
        close();
    });

    _lightboxEl.querySelector(".js-download").addEventListener("click", () => {
        const link = document.createElement("a");
        link.href = imageUrl;
        link.download = meta.imageName || "ai_generated.png";
        link.click();
    });

    document.body.appendChild(_lightboxEl);
}

// ─── Register all DOM listeners after the DOM is ready ───────────────────────

function registerDomListeners() {
    // Intercept "Use This Image" button clicks to show lightbox preview first
    document.addEventListener("click", (ev) => {
        const btn = ev.target.closest("[name='action_apply_image_line']");
        if (!btn) return;

        const row = btn.closest("tr.o_data_row");
        if (!row) return;

        const imgEl = row.querySelector(".o_field_image img, .o_image img, img[src]");
        const imageUrl = imgEl ? imgEl.src : null;

        const cells = row.querySelectorAll("td");
        const provider = cells[1] ? cells[1].textContent.trim() : "";
        const style = cells[2] ? cells[2].textContent.trim() : "";

        if (!imageUrl) return;

        ev.stopPropagation();
        ev.preventDefault();

        openLightbox(
            imageUrl,
            { imageName: "ai_generated.png", provider, style },
            () => {
                btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: false }));
            }
        );
    });

    // Auto-scroll bulk progress log textarea
    const progressObserver = new MutationObserver(() => {
        document.querySelectorAll(".o_field_widget[name='bulk_progress_log'] textarea").forEach((ta) => {
            ta.scrollTop = ta.scrollHeight;
        });
    });
    progressObserver.observe(document.body, { childList: true, subtree: true });

    // Clamp num_variants to 1–4 client-side
    document.addEventListener("change", (ev) => {
        const input = ev.target.closest(".o_field_widget[name='num_variants'] input");
        if (!input) return;
        const val = parseInt(input.value, 10);
        if (val > 4) { input.value = 4; input.dispatchEvent(new Event("input", { bubbles: true })); }
        if (val < 1) { input.value = 1; input.dispatchEvent(new Event("input", { bubbles: true })); }
    });
}

// Guard: run after DOM is ready (body may not exist during module parsing)
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", registerDomListeners);
} else {
    registerDomListeners();
}

export { AiImageLightbox };