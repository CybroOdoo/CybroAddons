/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeBuildCraft = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    
    start: function () {
        this._super.apply(this, arguments);
        this._initHamburger();
        this._initNavbarScroll();
        this._initScrollReveal();
        this._initProjectFilter();
        this._initProjectsPageFilter();
        this._initBlogFilter();
        this._initFaqToggle();
        this._initContactFormValidation();
    },

    // ... keeping other methods intact, just adding the new one

    _initProjectsPageFilter: function () {
        const tabs = this.el.querySelectorAll('.project-filter-tab');
        const cards = this.el.querySelectorAll('#projects-grid > .project-grid-card');

        if (tabs.length > 0 && !tabs[0].dataset.initialized) {
            tabs.forEach(tab => {
                tab.dataset.initialized = 'true';
                tab.addEventListener('click', () => {
                    tabs.forEach(t => {
                        t.classList.remove('active', 'bg-primary', 'text-primary-foreground', 'border-primary');
                        t.classList.add('bg-card', 'text-foreground', 'border-border');
                    });
                    tab.classList.add('active', 'bg-primary', 'text-primary-foreground', 'border-primary');
                    tab.classList.remove('bg-card', 'text-foreground', 'border-border');

                    const filter = tab.dataset.filter;
                    cards.forEach(card => {
                        const match = filter === 'all' || card.dataset.category === filter;
                        card.style.display = match ? '' : 'none';
                    });
                });
            });
        }
    },

    _initHamburger: function () {
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        const iconHamburger = document.getElementById('icon-hamburger');
        const iconClose = document.getElementById('icon-close');

        if (menuToggle && !menuToggle.dataset.initialized) {
            menuToggle.dataset.initialized = 'true';
            menuToggle.addEventListener('click', () => {
                const isOpen = mobileMenu.classList.toggle('open');
                iconHamburger.style.display = isOpen ? 'none' : 'block';
                iconClose.style.display = isOpen ? 'block' : 'none';
            });
        }
    },

    _initNavbarScroll: function () {
        const navbar = document.getElementById('navbar');
        if (navbar && !navbar.dataset.scrollInitialized) {
            navbar.dataset.scrollInitialized = 'true';
            window.addEventListener('scroll', () => {
                navbar.classList.toggle('scrolled', window.scrollY > 60);
            }, { passive: true });
        }
    },

    _initScrollReveal: function () {
        // Always re-query elements to catch newly loaded Ajax content
        const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
        if (revealEls.length > 0) {
            const revObserver = new IntersectionObserver((entries) => {
                entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            revealEls.forEach(el => revObserver.observe(el));
        }
    },

    _initProjectFilter: function () {
        const filterBtns = document.querySelectorAll('.filter-btn');
        const projectCards = document.querySelectorAll('.project-card');

        if (filterBtns.length > 0 && !filterBtns[0].dataset.initialized) {
            filterBtns.forEach(btn => {
                btn.dataset.initialized = 'true';
                btn.addEventListener('click', () => {
                    const filter = btn.dataset.filter;

                    filterBtns.forEach(b => {
                        b.classList.remove('bg-dark', 'text-white', 'border-dark');
                        b.classList.add('bg-background', 'text-muted-foreground', 'border-border');
                    });
                    btn.classList.remove('bg-background', 'text-muted-foreground', 'border-border');
                    btn.classList.add('bg-dark', 'text-white', 'border-dark');

                    projectCards.forEach(card => {
                        const match = filter === 'all' || card.dataset.category === filter;
                        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        if (match) {
                            card.style.opacity = '1';
                            card.style.transform = 'scale(1)';
                            card.style.display = '';
                        } else {
                            card.style.opacity = '0';
                            card.style.transform = 'scale(0.95)';
                            setTimeout(() => {
                                if (card.dataset.category !== filter && filter !== 'all') {
                                    card.style.display = 'none';
                                }
                            }, 300);
                        }
                    });
                });
            });
        }
    },

    _initBlogFilter: function () {
        const tabs = this.el.querySelectorAll('.filter-tab');
        const cards = this.el.querySelectorAll('#articles-grid > .blog-card');

        if (tabs.length > 0 && !tabs[0].dataset.initialized) {
            tabs.forEach(tab => {
                tab.dataset.initialized = 'true';
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    const filter = tab.dataset.filter;

                    cards.forEach(card => {
                        if (filter === 'all' || card.dataset.category === filter) {
                            card.style.display = '';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                });
            });
        }
    },

    _initFaqToggle: function () {
        const faqTriggers = this.el.querySelectorAll('.faq-trigger');
        if (faqTriggers.length > 0 && !faqTriggers[0].dataset.initialized) {
            faqTriggers.forEach(btn => {
                btn.dataset.initialized = 'true';
                btn.addEventListener('click', () => {
                    const body = btn.nextElementSibling;
                    const arrow = btn.querySelector('.faq-arrow');
                    const isOpen = !body.classList.contains('hidden');

                    // Close all
                    this.el.querySelectorAll('.faq-body').forEach(b => b.classList.add('hidden'));
                    this.el.querySelectorAll('.faq-arrow').forEach(a => a.style.transform = '');

                    // Open current if it was closed
                    if (!isOpen) {
                        body.classList.remove('hidden');
                        arrow.style.transform = 'rotate(180deg)';
                    }
                });
            });
        }
    },

    _initContactFormValidation: function () {
        const formSection = this.el.querySelector('.buildcraft-contact-form');
        if (!formSection) return;

        const form = formSection.querySelector('form');
        const submitBtn = formSection.querySelector('.s_website_form_send');
        if (!form || !submitBtn || submitBtn.dataset.validationInitialized) return;

        submitBtn.dataset.validationInitialized = 'true';

        // Inject validation styles if not already present
        if (!document.getElementById('bc-form-validation-styles')) {
            const styleEl = document.createElement('style');
            styleEl.id = 'bc-form-validation-styles';
            styleEl.textContent = `
                .bc-field-error .s_website_form_input,
                .bc-field-error .form-input,
                .bc-field-error input,
                .bc-field-error textarea,
                .bc-field-error select {
                    border-color: #ef4444 !important;
                    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15) !important;
                }
                .bc-error-message {
                    color: #ef4444;
                    font-size: 0.75rem;
                    font-weight: 500;
                    margin-top: 0.25rem;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    animation: bc-error-appear 0.2s ease-out;
                }
                @keyframes bc-error-appear {
                    from { opacity: 0; transform: translateY(-4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .bc-field-error .s_website_form_label_content {
                    color: #ef4444 !important;
                }
            `;
            document.head.appendChild(styleEl);
        }

        // Helper: clear error from a field wrapper
        const clearFieldError = (fieldWrapper) => {
            fieldWrapper.classList.remove('bc-field-error');
            const existingMsg = fieldWrapper.querySelector('.bc-error-message');
            if (existingMsg) existingMsg.remove();
        };

        // Helper: set error on a field wrapper
        const setFieldError = (fieldWrapper, message) => {
            fieldWrapper.classList.add('bc-field-error');
            // Remove any prior error
            const existing = fieldWrapper.querySelector('.bc-error-message');
            if (existing) existing.remove();
            const errorSpan = document.createElement('span');
            errorSpan.className = 'bc-error-message';
            errorSpan.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> ' + message;
            fieldWrapper.appendChild(errorSpan);
        };

        // Auto-clear errors on user input
        form.addEventListener('input', (e) => {
            const fieldWrapper = e.target.closest('.s_website_form_field');
            if (fieldWrapper) clearFieldError(fieldWrapper);
        });
        form.addEventListener('change', (e) => {
            const fieldWrapper = e.target.closest('.s_website_form_field');
            if (fieldWrapper) clearFieldError(fieldWrapper);
        });

        // Intercept submit button click during capture phase (before Odoo's handler)
        submitBtn.addEventListener('click', (e) => {
            // Clear all previous errors
            form.querySelectorAll('.bc-field-error').forEach(el => clearFieldError(el));

            let isValid = true;
            let firstInvalidField = null;

            // Validate all required fields (s_website_form_required)
            const requiredFields = form.querySelectorAll('.s_website_form_required');
            requiredFields.forEach(fieldWrapper => {
                const input = fieldWrapper.querySelector('input, textarea, select');
                if (!input) return;

                const labelContent = fieldWrapper.querySelector('.s_website_form_label_content');
                const fieldName = labelContent ? labelContent.textContent.trim() : 'This field';
                const value = input.value.trim();

                if (!value) {
                    setFieldError(fieldWrapper, fieldName + ' is required');
                    isValid = false;
                    if (!firstInvalidField) firstInvalidField = input;
                    return;
                }

                // Email format validation
                if (input.type === 'email' && value) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        setFieldError(fieldWrapper, 'Please enter a valid email address');
                        isValid = false;
                        if (!firstInvalidField) firstInvalidField = input;
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                e.stopImmediatePropagation();
                if (firstInvalidField) {
                    firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => firstInvalidField.focus(), 400);
                }
            }
        }, true); // true = capture phase, fires before Odoo's handler
    }
});

// Since Odoo replaces #wrap but leaves #wrapwrap during soft navigation,
// we also attach a secondary widget specifically to #wrap to ensure
// the reveal logic fires whenever a new page is loaded.
publicWidget.registry.ThemeBuildCraftPage = publicWidget.Widget.extend({
    selector: '#wrap',
    start: function () {
        this._super.apply(this, arguments);
        const revealEls = this.el.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
        if (revealEls.length > 0) {
            const revObserver = new IntersectionObserver((entries) => {
                entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            revealEls.forEach(el => revObserver.observe(el));
        }
    }
});
