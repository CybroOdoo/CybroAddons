/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
export class SignupApprovalInteraction extends Interaction {
    static selector = ".oe_signup_form";  // same as in auth_signup
    dynamicContent = {
        _root: { "t-on-submit": this.onSubmit },
    };
    async onSubmit(ev) {
        ev.preventDefault();
        const form = this.el;
        const fileInputs = form.querySelectorAll(".get_attach");
        const email = form.querySelector("input[name='login']").value;
        const username = form.querySelector("input[name='name']").value;
        const password = form.querySelector("input[name='password']").value;
        const confirm_password=form.querySelector("input[name='confirm_password']").value;
        const data_array = [];
        for (const input of fileInputs) {
            const file = input.files[0];
            if (file) {
                const base64 = await this._readFileAsBase64(file);
                data_array.push(base64);
            }
        }
        await rpc("/web/signup/approve", {
            data: data_array,
            email,
            username,
            password,
            confirm_password,
        });
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
registry.category("public.interactions").add("website_signup_approval.signup", SignupApprovalInteraction);
