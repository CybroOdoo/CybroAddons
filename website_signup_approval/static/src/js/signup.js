import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class SignupApprovalInteraction extends Interaction {
    static selector = ".oe_signup_form";

    dynamicContent = {
        _root: { "t-on-submit.prevent": this.onSubmit },
    };

    async onSubmit(ev) {
        const form = this.el;
        const approvalMarker = form.querySelector(".is_signup_approval");
        if (!approvalMarker) {
            // Approval is disabled or token invitation: allow normal signup
            HTMLFormElement.prototype.submit.call(form);
            return;
        }

        this._clearError(form);

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const emailInput = form.querySelector("input[name='login']");
        const nameInput = form.querySelector("input[name='name']");
        const passwordInput = form.querySelector("input[name='password']");
        const confirmPasswordInput = form.querySelector(
            "input[name='confirm_password']"
        );

        const email = emailInput ? emailInput.value : "";
        const username = nameInput ? nameInput.value : "";
        const password = passwordInput ? passwordInput.value : "";
        const confirm_password = confirmPasswordInput
            ? confirmPasswordInput.value
            : "";

        if (password !== confirm_password) {
            this._showError(form, _t("Passwords do not match"));
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
        }

        const data_array = [];
        const fileInputs = form.querySelectorAll(".get_attach");
        for (const input of fileInputs) {
            const file = input.files[0];
            if (file) {
                const base64 = await this._readFileAsBase64(file);
                data_array.push(base64);
            }
        }

        try {
            const res = await rpc("/web/signup/approve", {
                data: data_array,
                email,
                username,
                password,
                confirm_password,
            });

            if (res && res.error) {
                this._showError(form, res.error);
                if (submitBtn) {
                    submitBtn.disabled = false;
                }
                return;
            }

            window.location.href = "/success";
        } catch (err) {
            this._showError(
                form,
                _t("An error occurred while submitting your request.")
            );
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }
    }

    _showError(form, message) {
        let errorEl = form.querySelector(".alert-danger");
        if (!errorEl) {
            errorEl = document.createElement("p");
            errorEl.className = "alert alert-danger";
            form.prepend(errorEl);
        }
        errorEl.textContent = message;
        errorEl.classList.remove("d-none");
    }

    _clearError(form) {
        const errorEl = form.querySelector(".alert-danger");
        if (errorEl) {
            errorEl.remove();
        }
    }

    _readFileAsBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
        });
    }
}

// Register in public interaction registry
registry.category("public.interactions").add(
    "website_signup_approval.signup", SignupApprovalInteraction
);
