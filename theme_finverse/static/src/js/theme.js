/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Mobile Menu Widget
publicWidget.registry.FinverseMobileMenu = publicWidget.Widget.extend({
    selector: ".header-container",
    disabledInEditableMode: true,
    start() {
        this._super(...arguments);
        const hamburgerMenu = this.el.querySelector("#hamburgerMenu");
        const mobileMenu    = this.el.querySelector("#mobileMenu");
        const backdrop      = this.el.querySelector("#mobileMenuBackdrop");
        const closeBtn      = this.el.querySelector("#mobileCloseBtn");
        const navbar        = this.el.querySelector("#finance-navbar");
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

            // Toggle on hamburger click
            hamburgerMenu.addEventListener("click", (e) => {
                e.stopPropagation();
                mobileMenu.classList.contains("active") ? closePanel() : openPanel();
            });

            // Close via dedicated close button
            if (closeBtn) {
                closeBtn.addEventListener("click", closePanel);
            }

            // Close via backdrop tap
            if (backdrop) {
                backdrop.addEventListener("click", closePanel);
            }

            // Close when a nav link is tapped
            mobileMenu.querySelectorAll(".nav-item a, .mobile-nav-actions a").forEach(link => {
                link.addEventListener("click", closePanel);
            });

            // Escape key
            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && mobileMenu.classList.contains("active")) {
                    closePanel();
                }
            });

            // Close if viewport grows above tablet breakpoint
            window.addEventListener("resize", () => {
                if (window.innerWidth > 1024 && mobileMenu.classList.contains("active")) {
                    closePanel();
                }
            }, { passive: true });
        }

        // Sticky navbar logic
        if (navbar) {
            const updateSticky = () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                navbar.classList.toggle("sticky", scrollTop >= 10);
            };
            window.addEventListener("scroll", updateSticky, { passive: true });
            updateSticky();
        }

        return Promise.resolve();
    },
});

// Animations and Interactions
publicWidget.registry.FinverseInteractions = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    disabledInEditableMode: true,
    start() {
        this._super(...arguments);
        // Scroll to top
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

        // Intersetion Observer for animation
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

        // Service card hovers
        this.el.querySelectorAll(".service-card").forEach(card => {
            card.addEventListener("mouseenter", () => card.style.transform = "translateY(-8px)");
            card.addEventListener("mouseleave", () => card.style.transform = "translateY(0)");
        });

        // Smooth scrolling
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

// FAQ Accordion Widget
publicWidget.registry.FinverseFAQ = publicWidget.Widget.extend({
    selector: ".finance-faq",

    start() {
        this._super(...arguments);
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
        const isActive = clickedItem.classList.contains("active");
        
        // Close all items
        this.faqItems.forEach(item => {
            item.classList.remove("active");
            const icon = item.querySelector(".fa");
            if (icon) {
                icon.classList.remove("fa-chevron-up");
                icon.classList.add("fa-chevron-down");
            }
        });

        // Toggle clicked item
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

// Insights Category Tabs Widget
publicWidget.registry.FinverseInsightsTabs = publicWidget.Widget.extend({
    selector: ".insights-section",
    disabledInEditableMode: false,

    events: {
        'click .filter-btn': '_onFilterBtnClick',
        'mousedown .filter-btn': '_onFilterBtnMousedown',
    },

    start() {
        this._super(...arguments);
        return Promise.resolve();
    },

    _onFilterBtnClick(ev) {
        ev.preventDefault();
        // If in edit mode, let mousedown handle it to avoid conflicts with editor clicks
        if (this.editableMode || document.body.classList.contains('editor_enable')) {
            return;
        }
        this._switchTab(ev.currentTarget);
    },

    _onFilterBtnMousedown(ev) {
        // If in edit mode, switch tab on mousedown
        if (this.editableMode || document.body.classList.contains('editor_enable')) {
            this._switchTab(ev.currentTarget);
        }
    },

    _switchTab(clickedBtn) {
        const buttons = this.el.querySelectorAll(".filter-btn");
        const index = Array.from(buttons).indexOf(clickedBtn);
        if (index === -1) return;
        // Toggle active class on buttons
        buttons.forEach((btn, i) => {
            btn.classList.toggle("active", i === index);
        });
        // Toggle visibility on tab panes
        const tabIds = ["#tab-all", "#tab-market", "#tab-wealth", "#tab-strategy", "#tab-innovation"];
        tabIds.forEach((id, i) => {
            const pane = this.el.querySelector(id);
            if (pane) {
                if (i === index) {
                    pane.classList.remove("d-none");
                    pane.classList.add("active");
                } else {
                    pane.classList.add("d-none");
                    pane.classList.remove("active");
                }
            }
        });
    },
});
