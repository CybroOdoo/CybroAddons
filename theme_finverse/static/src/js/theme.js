/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// ─── Mobile Menu Widget ────────────────────────────────────────────────────
publicWidget.registry.FinverseMobileMenu = publicWidget.Widget.extend({
    selector: ".header-container",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();

        const hamburgerMenu = this.el.querySelector("#hamburgerMenu");
        const mobileMenu    = this.el.querySelector("#mobileMenu");
        const backdrop      = this.el.querySelector("#mobileMenuBackdrop");
        const closeBtn      = this.el.querySelector("#mobileCloseBtn");
        if (hamburgerMenu && mobileMenu) {
            const closePanel = () => {
                hamburgerMenu.classList.remove("active");
                mobileMenu.classList.remove("active");
                hamburgerMenu.setAttribute("aria-expanded", "false");
                document.body.classList.remove("mobile-open");
            };

            const openPanel = () => {
                hamburgerMenu.classList.add("active");
                mobileMenu.classList.add("active");
                hamburgerMenu.setAttribute("aria-expanded", "true");
                document.body.classList.add("mobile-open");
            };

            hamburgerMenu.addEventListener("click", (e) => {
                e.stopPropagation();
                mobileMenu.classList.contains("active") ? closePanel() : openPanel();
            });

            if (closeBtn) {
                closeBtn.addEventListener("click", closePanel);
            }

            if (backdrop) {
                backdrop.addEventListener("click", closePanel);
            }

            mobileMenu.querySelectorAll(".nav-item a, .mobile-nav-actions a").forEach(link => {
                link.addEventListener("click", closePanel);
            });

            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && mobileMenu.classList.contains("active")) {
                    closePanel();
                }
            });

            window.addEventListener("resize", () => {
                if (window.innerWidth > 1024 && mobileMenu.classList.contains("active")) {
                    closePanel();
                }
            }, { passive: true });
        }

        return Promise.resolve();
    },
});

publicWidget.registry.FinverseStickyNavbar = publicWidget.Widget.extend({
    selector: ".navbar",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();

        this._scrolled = false;
        this._updateSticky = this._updateSticky.bind(this);

        // Use the Odoo scrollable container if available, fallback to window
        this._scrollTarget = this.el.closest(".o_website_main") ||
                             document.querySelector("#wrapwrap") ||
                             window;

        this._scrollTarget.addEventListener("scroll", this._updateSticky, { passive: true });

        // Run once on start without adding class (page just loaded at top)
        this._updateSticky();

        return Promise.resolve();
    },

    destroy() {
        if (this._scrollTarget) {
            this._scrollTarget.removeEventListener("scroll", this._updateSticky);
        }
        this._super(...arguments);
    },

    _updateSticky() {
        // Get scrollTop from the correct container
        const scrollTop = this._scrollTarget === window
            ? (window.pageYOffset || document.documentElement.scrollTop)
            : this._scrollTarget.scrollTop;

        if (scrollTop > 0) {
            // Scrolled away from top → add class
            if (!this.el.classList.contains("sticky")) {
                this.el.classList.add("sticky");
            }
        } else {
            // Back at top → remove class
            if (this.el.classList.contains("sticky")) {
                this.el.classList.remove("sticky");
            }
        }
    },
});

// ─── Animations and Interactions ──────────────────────────────────────────
publicWidget.registry.FinverseInteractions = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();

        const scrollToTopBtn = this.el.querySelector("#scrollToTop");
        if (scrollToTopBtn) {
            window.addEventListener("scroll", () => {
                if (window.pageYOffset > 300) {
                    scrollToTopBtn.classList.add("visible");
                } else {
                    scrollToTopBtn.classList.remove("visible");
                }
            });

            scrollToTopBtn.addEventListener("click", () => {
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }

        const observerOptions = { threshold: 0.1, rootMargin: "0px 0px -50px 0px" };
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("animate-in");
                }
            });
        }, observerOptions);

        this.el.querySelectorAll("section").forEach(section => {
            observer.observe(section);
        });

        this.el.querySelectorAll(".service-card").forEach(card => {
            card.addEventListener("mouseenter", () => card.style.transform = "translateY(-8px)");
            card.addEventListener("mouseleave", () => card.style.transform = "translateY(0)");
        });

        this.el.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener("click", function (e) {
                const targetId = this.getAttribute("href");
                if (targetId && targetId !== '#') {
                    const targetElement = document.querySelector(targetId);
                    if (targetElement) {
                        e.preventDefault();
                        targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }
            });
        });

        return Promise.resolve();
    }
});

// ─── FAQ Accordion Widget ──────────────────────────────────────────────────
publicWidget.registry.FinverseFAQ = publicWidget.Widget.extend({
    selector: ".finance-faq",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();

        this.faqItems = this.el.querySelectorAll(".faq-item");
        this.faqItems.forEach(item => {
            const question = item.querySelector(".faq-question");
            if (question) {
                question.addEventListener("click", () => this._onQuestionClick(item));
            }
        });
        return Promise.resolve();
    },

    _onQuestionClick(clickedItem) {
        if (!clickedItem || !this.faqItems) return;

        const isActive = clickedItem.classList.contains("active");

        this.faqItems.forEach(item => {
            item.classList.remove("active");
            const icon = item.querySelector(".fa");
            if (icon) {
                icon.classList.remove("fa-chevron-up");
                icon.classList.add("fa-chevron-down");
            }
        });

        if (!isActive) {
            clickedItem.classList.add("active");
            const icon = clickedItem.querySelector(".fa");
            if (icon) {
                icon.classList.remove("fa-chevron-down");
                icon.classList.add("fa-chevron-up");
            }
        }
    },
});

// ─── Insights Category Tabs Widget ────────────────────────────────────────
// disabledInEditableMode: false so tabs work in both frontend AND website editor.
// In edit mode, mousedown is used so the click doesn't conflict with editor selection.
publicWidget.registry.FinverseInsightsTabs = publicWidget.Widget.extend({
    selector: ".insights-section",
    disabledInEditableMode: false,

    events: {
        'click .filter-btn': '_onFilterBtnClick',
        'mousedown .filter-btn': '_onFilterBtnMousedown',
    },

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();
        return Promise.resolve();
    },

    _onFilterBtnClick(ev) {
        ev.preventDefault();
        // In edit mode let mousedown handle it to avoid conflicts with editor clicks
        if (this.editableMode || document.body.classList.contains('editor_enable')) {
            return;
        }
        this._switchTab(ev.currentTarget);
    },

    _onFilterBtnMousedown(ev) {
        // In edit mode switch tab on mousedown so the editor doesn't swallow the event
        if (this.editableMode || document.body.classList.contains('editor_enable')) {
            this._switchTab(ev.currentTarget);
        }
    },

    _switchTab(clickedBtn) {
        if (!clickedBtn || !this.el) return;

        const buttons = this.el.querySelectorAll(".filter-btn");
        const index = Array.from(buttons).indexOf(clickedBtn);
        if (index === -1) return;

        buttons.forEach((btn, i) => {
            btn.classList.toggle("active", i === index);
        });

        const tabIds = ["#tab-all", "#tab-market", "#tab-wealth", "#tab-strategy", "#tab-innovation"];
        tabIds.forEach((id, i) => {
            const pane = this.el.querySelector(id);
            if (!pane) return;
            if (i === index) {
                pane.classList.remove("d-none");
                pane.classList.add("active");
            } else {
                pane.classList.add("d-none");
                pane.classList.remove("active");
            }
        });
    },
});

// ─── Custom Newsletter Widget ──────────────────────────────────────────────
// Uses our own .finverse-newsletter-form div — does NOT use .js_subscribe so
// it avoids triggering the website_mass_mailing widget which crashes in Odoo 17.
publicWidget.registry.FinverseNewsletter = publicWidget.Widget.extend({
    selector: ".finverse-newsletter-form",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        if (!this.el) return Promise.resolve();

        const btn = this.el.querySelector("#finverse_newsletter_btn");
        const input = this.el.querySelector("#finverse_newsletter_email");
        const msg = this.el.querySelector("#finverse_newsletter_msg");

        if (btn && input) {
            btn.addEventListener("click", async () => {
                const email = input.value ? input.value.trim() : "";
                if (!email || !email.match(/.+@.+\..+/)) {
                    if (msg) {
                        msg.textContent = "Please enter a valid email address.";
                        msg.style.color = "#f87171";
                        msg.classList.remove("d-none");
                    }
                    return;
                }

                btn.disabled = true;
                btn.textContent = "Subscribing…";

                try {
                    await fetch("/web/dataset/call_kw", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            jsonrpc: "2.0",
                            method: "call",
                            params: {
                                model: "mailing.contact",
                                method: "create",
                                args: [{ email: email, name: email }],
                                kwargs: {},
                            },
                        }),
                    });
                    input.value = "";
                    btn.textContent = "Subscribed!";
                    if (msg) {
                        msg.textContent = "Thanks for subscribing! We'll be in touch.";
                        msg.style.color = "#34d399";
                        msg.classList.remove("d-none");
                    }
                } catch (_e) {
                    btn.disabled = false;
                    btn.textContent = "Subscribe";
                    if (msg) {
                        msg.textContent = "Something went wrong. Please try again.";
                        msg.style.color = "#f87171";
                        msg.classList.remove("d-none");
                    }
                }
            });
        }

        return Promise.resolve();
    },
});
