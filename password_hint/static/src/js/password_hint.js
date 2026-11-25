/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PasswordHint extends Interaction {
    static selector = "#Password_login_hint";
    dynamicContent = {
        _root: { "t-on-click.prevent": this.onClick },
    };

    async onClick() {
        const loginInput = document.querySelector("#login");
        const login = loginInput?.value?.trim();

        if (!login) {
            this.showModal("Please enter Email.");
            return;
        }

        try {
            const data = await this.waitFor(
                rpc("/website/password/hint", {
                    login: login,
                })
            );

            this.showModal(data || "No password hint found.");
        } catch (error) {
            console.error("Password hint request failed:", error);
        }
    }

    showModal(message) {
        const existingModal = document.querySelector("#popup_error_message");

        if (existingModal) {
            existingModal.remove();
        }

        const modalHTML = `
            <div class="modal show d-block"
                 id="popup_error_message"
                 tabindex="-1"
                 role="dialog"
                 style="background-color: rgba(0, 0, 0, 0.5);">

                <div class="modal-dialog modal-dialog-centered" role="document">
                    <div class="modal-content">

                        <div class="modal-header">
                            <h5 class="modal-title">
                                Password Hint
                            </h5>

                            <button type="button"
                                    class="btn-close"
                                    aria-label="Close">
                            </button>
                        </div>

                        <div class="modal-body">
                            <p class="mb-0"></p>
                        </div>

                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML("beforeend", modalHTML);

        const modal = document.querySelector("#popup_error_message");
        const messagePara = modal.querySelector(".modal-body p");
        if (messagePara) {
            messagePara.textContent = message;
        }

        modal.querySelector(".btn-close").addEventListener("click", () => {
            modal.remove();
        });

        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
}

registry.category("public.interactions").add(
    "password_hint",
    PasswordHint
);