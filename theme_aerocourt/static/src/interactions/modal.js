/** Modal dialog shared by the booking, session and membership forms. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { escapeHTML, prefersReducedMotion } from "./utils";

const modalRef = { current: null };

/** The modal of the page, shared by the booking, session and membership flows. */
export const getModal = () => modalRef.current;

/** The modal body: it exists in the layout even before the modal starts. */
export const getModalBody = () => document.getElementById("modalBody");

/**
 * The dialog of the layout. Other interactions put their content in it with
 * `getModal().open(html)`.
 */
export class AcModal extends Interaction {
    static selector = "#modal";
    dynamicContent = {
        _root: {
            "t-on-cancel.prevent": this.close,
            "t-on-click": this.onClick,
        },
        ".ac-modal__grab": {
            "t-on-pointerdown.noUpdate": this.onDragStart,
            "t-on-pointermove.noUpdate": this.onDragMove,
            "t-on-pointerup.noUpdate": this.onDragEnd,
            "t-on-pointercancel.noUpdate": this.onDragEnd,
        },
    };

    setup() {
        this.body = this.el.querySelector("#modalBody");
        this.panel = this.el.querySelector(".ac-modal__panel");
        this.returnFocusTo = null;
        this.onCloseCallback = null;
        this.closing = false;
        this.dragStart = null;
        modalRef.current = this;
        this.registerCleanup(() => {
            modalRef.current = null;
        });
    }

    /**
     * Shows content in the modal, or swaps the content when it is already open.
     *
     * @param {string} html
     * @param {{wide?: boolean, onClose?: Function}} options
     */
    open(html, { wide = false, onClose = null } = {}) {
        if (this.el.open) {
            this.body.innerHTML = html;
            this.body.scrollTop = 0;
            this.onCloseCallback = onClose;
            this.body.querySelector("#modalTitle")?.focus({ preventScroll: true });
            return;
        }
        this.returnFocusTo = document.activeElement;
        this.onCloseCallback = onClose;
        this.body.innerHTML = html;
        this.body.scrollTop = 0;
        this.el.classList.toggle("ac-modal--wide", wide);
        this.el.showModal();
        document.documentElement.classList.add("ac-modal-open");
        this.body.querySelector("#modalTitle")?.focus({ preventScroll: true });
        requestAnimationFrame(() => this.el.classList.add("is-open"));
    }

    close() {
        if (!this.el.open || this.closing) {
            return;
        }
        this.closing = true;
        this.el.classList.remove("is-open");
        const finish = () => {
            this.el.close();
            this.body.innerHTML = "";
            document.documentElement.classList.remove("ac-modal-open");
            this.closing = false;
            const callback = this.onCloseCallback;
            this.onCloseCallback = null;
            callback?.();
            if (this.returnFocusTo && document.contains(this.returnFocusTo)) {
                this.returnFocusTo.focus({ preventScroll: true });
            }
        };
        if (prefersReducedMotion()) {
            finish();
        } else {
            this.waitForTimeout(finish, 320);
        }
    }

    /** Replaces the content with a success view and moves the focus to it. */
    showSuccess({ title, text, reference, details = [], note = "", link = null }) {
        this.body.innerHTML = `
            <div class="ac-modal-content ac-success">
              <span class="ac-success__icon"><i class="ac-icon ac-i-ph-check-bold" aria-hidden="true"></i></span>
              <h2 class="ac-modal-title" id="modalTitle" tabindex="-1">${title}</h2>
              <p class="ac-modal-lead">${text}</p>
              ${reference ? `<p class="ac-success__ref">${_t("Reference")} · ${escapeHTML(reference)}</p>` : ""}
              ${details.length ? `<dl class="ac-detail-grid">${details.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>` : ""}
              ${note ? `<p class="ac-modal-note"><i class="ac-icon ac-i-ph-info-bold" aria-hidden="true"></i> ${note}</p>` : ""}
              <div class="ac-modal-actions">
                <button type="button" class="ac-btn ac-btn--primary" data-modal-close>${_t("Done")}</button>
                ${link ? `<a class="ac-btn ac-btn--ghost" href="${link.href}">${link.label} <i class="ac-icon ac-i-ph-arrow-right-bold" aria-hidden="true"></i></a>` : ""}
              </div>
            </div>`;
        this.body.scrollTop = 0;
        this.body.querySelector("#modalTitle").focus({ preventScroll: true });
    }

    onClick(ev) {
        if (ev.target === this.el || ev.target.closest("[data-modal-close]")) {
            this.close();
        }
    }

    // Bottom sheet on phones: drag the grab handle down to dismiss
    onDragStart(ev) {
        this.dragStart = ev.clientY;
        ev.currentTarget.setPointerCapture(ev.pointerId);
        this.panel.classList.add("is-dragging");
    }

    onDragMove(ev) {
        if (this.dragStart !== null) {
            this.panel.style.setProperty("--drag", `${Math.max(0, ev.clientY - this.dragStart)}px`);
        }
    }

    onDragEnd(ev) {
        if (this.dragStart === null) {
            return;
        }
        const distance = ev.clientY - this.dragStart;
        this.dragStart = null;
        this.panel.classList.remove("is-dragging");
        this.panel.style.removeProperty("--drag");
        if (distance > 110) {
            this.close();
        }
    }
}

registry.category("public.interactions").add("theme_aerocourt.modal", AcModal);
