/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ScrollAnimation extends Interaction {
    static selector = ".images";

    setup() {
        super.setup();
        this.onScrollBound = this.onScroll.bind(this);
        window.addEventListener('scroll', this.onScrollBound);
        window.addEventListener('resize', this.onScrollBound);
        this.onScroll();
    }
    
    destroy() {
        window.removeEventListener('scroll', this.onScrollBound);
        window.removeEventListener('resize', this.onScrollBound);
        super.destroy();
    }

    onScroll() {
        const images = this.el.querySelectorAll('.inline-photo');
        images.forEach((element) => {
            if (this.isElementInViewport(element)) {
                element.classList.add('is-visible');
            } else {
                element.classList.remove('is-visible');
            }
        });
    }

    isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) && 
            rect.bottom >= 0
        );
    }
}

export class ContactFormValidation extends Interaction {
    static selector = "#contactus_form";

    setup() {
        super.setup();
        const submitBtn = this.el.querySelector('.o_website_form_send');
        if (submitBtn) {
            this.onSubmitBound = this._onSubmit.bind(this);
            // Use capture phase (true) to intercept the click before Odoo's standard event handler
            submitBtn.addEventListener('click', this.onSubmitBound, true);
        }
    }
    
    destroy() {
        const submitBtn = this.el.querySelector('.o_website_form_send');
        if (submitBtn && this.onSubmitBound) {
            submitBtn.removeEventListener('click', this.onSubmitBound, true);
        }
        super.destroy();
    }

    _onSubmit(ev) {
        const name = this.el.querySelector('input[name="name"]');
        const email = this.el.querySelector('input[name="email_from"]');
        const phone = this.el.querySelector('input[name="phone"]');
        const errorMsg = this.el.querySelector('#contact_form_error');

        let valid = true;

        if (name) name.classList.remove('is-invalid');
        if (email) email.classList.remove('is-invalid');
        if (phone) phone.classList.remove('is-invalid');
        if (errorMsg) errorMsg.style.display = 'none';

        if (name && !name.value.trim()) {
            valid = false;
            name.classList.add('is-invalid');
        }

        if (phone && !phone.value.trim()) {
            valid = false;
            phone.classList.add('is-invalid');
        }

        if (email && !email.value.trim()) {
            valid = false;
            email.classList.add('is-invalid');
        }

        if (!valid) {
            ev.preventDefault();
            ev.stopPropagation();
            ev.stopImmediatePropagation(); // Stop other listeners (Odoo submission) from running
            if (errorMsg) errorMsg.style.display = 'block';
        }
    }
}

registry.category("public.interactions").add("theme_watchhut.ScrollAnimation", ScrollAnimation);
registry.category("public.interactions").add("theme_watchhut.ContactFormValidation", ContactFormValidation);
