/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class QuickViewModal extends Interaction {
    static selector = ".oe_website_sale";

    dynamicContent = {
        "a.c-product-quick-view-action": {
            "t-on-click.prevent": this.onQuickViewClick,
        },
    };

    async onQuickViewClick(ev) {
        const button = ev.target.closest("a.c-product-quick-view-action") || ev.currentTarget;
        const productId = button?.dataset?.productId;

        if (!productId) {
            return;
        }

        let html;
        try {
            html = await this.waitFor(
                rpc("/c_quick_view/get_quick_view_html", { product_id: productId })
            );
        } catch (err) {
            if (this.services?.notification) {
                this.services.notification.add(
                    err.data?.message || "Could not load quick view content.",
                    { type: "danger" }
                );
            }
            return;
        }

        if (typeof html !== "string" || !html.trim()) {
            if (this.services?.notification) {
                this.services.notification.add(
                    "Could not load quick view content.",
                    { type: "danger" }
                );
            }
            return;
        }

        this.showModal(html);
    }

    showModal(template) {
        document.querySelectorAll("#c_product_quick_view_modal, #c_quick_view_error_modal, .c-quick-view-backdrop").forEach((el) => el.remove());
        document.body.classList.remove("modal-open");
        document.body.classList.remove("c-quick-view-open");

        const wrapper = document.createElement("div");
        wrapper.innerHTML = template.trim();
        const modalEl = wrapper.querySelector(".modal") || wrapper.firstElementChild;

        if (!modalEl) {
            return;
        }

        document.body.appendChild(modalEl);

        const closeModal = () => {
            modalEl.classList.remove("show");
            modalEl.classList.remove("c-quick-view-modal-open");
            document.body.classList.remove("modal-open");
            document.body.classList.remove("c-quick-view-open");
            const backdrop = document.querySelector(".c-quick-view-backdrop");
            if (backdrop) {
                backdrop.remove();
            }
            setTimeout(() => modalEl.remove(), 250);
        };

        try {
            const bs = window.bootstrap || (typeof bootstrap !== "undefined" ? bootstrap : null);
            if (bs && bs.Modal) {
                const modal = bs.Modal.getOrCreateInstance ? bs.Modal.getOrCreateInstance(modalEl) : new bs.Modal(modalEl);
                modal.show();
                modalEl.addEventListener("hidden.bs.modal", () => modalEl.remove(), { once: true });
                return;
            }
        } catch {
            // Use the CSS fallback below when Bootstrap cannot open this modal.
        }

        modalEl.classList.add("c-quick-view-modal-open");
        modalEl.removeAttribute("aria-hidden");
        modalEl.setAttribute("aria-modal", "true");
        modalEl.setAttribute("role", "dialog");

        const backdrop = document.createElement("div");
        backdrop.className = "modal-backdrop fade show c-quick-view-backdrop";
        document.body.appendChild(backdrop);

        document.body.classList.add("modal-open");
        document.body.classList.add("c-quick-view-open");
        setTimeout(() => {
            modalEl.classList.add("show");
        }, 15);

        modalEl.querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                closeModal();
            });
        });

        modalEl.addEventListener("click", (e) => {
            if (e.target === modalEl) {
                closeModal();
            }
        });

        const escHandler = (e) => {
            if (e.key === "Escape") {
                closeModal();
                document.removeEventListener("keydown", escHandler);
            }
        };
        document.addEventListener("keydown", escHandler);
    }
}

registry
    .category("public.interactions")
    .add("ecommerce_quick_view.QuickViewModal", QuickViewModal);
