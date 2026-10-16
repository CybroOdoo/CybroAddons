/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeCordage = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    start: function () {
        this._initFaqCollapse();
        this._initSmoothScroll();
        this._initFormValidation();
        return this._super.apply(this, arguments);
    },
    /**
     * Initializes the custom FAQ collapse animation on the contact page.
     */
    _initFaqCollapse: function () {
        const faqQuestions = this.el.querySelectorAll('.faq-q');
        faqQuestions.forEach(btn => {
            btn.addEventListener('click', () => {
                const answer = btn.nextElementSibling;
                const arrow = btn.querySelector('.arrow');
                if (answer) {
                    const isOpen = answer.classList.contains('open');
                    // Collapse all first
                    this.el.querySelectorAll('.faq-a').forEach(a => {
                        a.classList.remove('open');
                        a.style.maxHeight = null;
                    });
                    this.el.querySelectorAll('.faq-q').forEach(q => {
                        q.classList.remove('open');
                    });
                    if (!isOpen) {
                        answer.classList.add('open');
                        btn.classList.add('open');
                        answer.style.maxHeight = answer.scrollHeight + "px";
                    }
                }
            });
        });
    },
    /**
     * Setups smooth scrolling behaviors for anchor tags.
     */
    _initSmoothScroll: function () {
        this.el.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
    },
    /**
     * Adds native constraint validation feedback before Odoo/custom actions run.
     */
    _initFormValidation: function () {
        const validateForm = (form) => {
            if (!form || form.checkValidity()) {
                form?.classList.remove('cordage-form-invalid');
                return true;
            }
            form.classList.add('cordage-form-invalid');
            form.reportValidity();
            return false;
        };
        this.el.querySelectorAll('form.cordage-validated-form, .s_website_form form').forEach(form => {
            form.addEventListener('submit', (ev) => {
                if (!validateForm(form)) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
            }, true);
        });
        this.el.querySelectorAll('.s_website_form_send').forEach(button => {
            button.addEventListener('click', (ev) => {
                const form = button.closest('form');
                if (!validateForm(form)) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
            }, true);
        });
        this.el.querySelectorAll('.js_subscribe_btn').forEach(button => {
            button.addEventListener('click', (ev) => {
                const wrapper = button.closest('.js_subscribe_wrap');
                const input = wrapper?.querySelector('.js_subscribe_value');
                if (input && !input.checkValidity()) {
                    input.classList.add('cordage-input-invalid');
                    input.reportValidity();
                    ev.preventDefault();
                    ev.stopPropagation();
                }
            }, true);
        });
        this.el.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('input', () => {
                field.classList.remove('cordage-input-invalid');
                field.closest('form')?.classList.remove('cordage-form-invalid');
            });
        });
    }
});
