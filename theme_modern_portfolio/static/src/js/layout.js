/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Theme Modern Portfolio - Layout Widget
 * Handles header shadow, mobile menu, dropdowns, and scroll animations
 */
publicWidget.registry.ModernPortfolioLayout = publicWidget.Widget.extend({
    selector: "#wrapwrap",

    /**
     * @override
     */
    start: function () {
        this._initModernPortfolio();
        return this._super.apply(this, arguments);
    },

    /**
     * Initialize all layout-related interactions
     * @private
     */
    _initModernPortfolio: function () {
        const headerEl = this.el.querySelector("header#top");
        const menuToggle = this.el.querySelector(".menu-toggle");
        const dropdownFields = this.el.querySelectorAll(".dropdown-field");

        // Header shadow on scroll
        if (headerEl) {
            window.addEventListener("scroll", () => {
                if (window.scrollY > 10) {
                    headerEl.classList.add("header-shadow");
                } else {
                    headerEl.classList.remove("header-shadow");
                }
            });
        }

        // Mobile menu toggle
        if (menuToggle && headerEl) {
            menuToggle.addEventListener("click", (e) => {
                e.stopPropagation();
                headerEl.classList.toggle("menu-open");
            });

            // Close menu when clicking nav links
            headerEl.querySelectorAll(".menucol a").forEach((link) => {
                link.addEventListener("click", () => {
                    headerEl.classList.remove("menu-open");
                });
            });

            // Close menu when clicking outside
            document.addEventListener("click", (e) => {
                if (!headerEl.contains(e.target)) {
                    headerEl.classList.remove("menu-open");
                }
            });
        }

        // Dropdown functionality
        dropdownFields.forEach((field) => {
            const header = field.querySelector(".dropdown-header");
            const options = field.querySelectorAll(".dropdown-option");

            if (!header) return;

            header.addEventListener("click", (e) => {
                e.stopPropagation();
                field.classList.toggle("active");

                // Close other dropdowns
                dropdownFields.forEach((otherField) => {
                    if (otherField !== field) {
                        otherField.classList.remove("active");
                    }
                });
            });

            options.forEach((option) => {
                option.addEventListener("click", (e) => {
                    e.stopPropagation();
                    const span = header.querySelector("span:first-child");
                    if (span) span.textContent = option.textContent;
                    field.classList.remove("active");
                });
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener("click", () => {
            dropdownFields.forEach((field) => field.classList.remove("active"));
        });

        // Gradient text animation for .subpara
        const subpara = this.el.querySelector(".subpara");
        if (subpara) {
            const startColor = [200, 200, 200];
            const endColor = [0, 0, 0];

            const text = subpara.textContent;
            const words = text.trim().split(/\s+/);
            subpara.innerHTML = words
                .map((word) => `<span class="word" style="color: rgb(200,200,200)">${word}</span>`)
                .join(" ");

            window.addEventListener("scroll", () => {
                const wordSpans = subpara.querySelectorAll(".word");
                const viewportHeight = window.innerHeight;

                wordSpans.forEach((span) => {
                    const wordRect = span.getBoundingClientRect();
                    const wordCenter = (wordRect.top + wordRect.bottom) / 2;
                    const screenCenter = viewportHeight / 2;

                    let wordProgress = 0;
                    if (wordCenter < screenCenter) {
                        wordProgress = 1;
                    } else if (wordCenter >= screenCenter && wordRect.top < viewportHeight) {
                        const distanceFromCenter = wordCenter - screenCenter;
                        const maxDistance = screenCenter;
                        wordProgress = 1 - distanceFromCenter / maxDistance;
                        wordProgress = Math.max(0, Math.min(1, wordProgress));
                    }

                    const r = Math.round(startColor[0] + (endColor[0] - startColor[0]) * wordProgress);
                    const g = Math.round(startColor[1] + (endColor[1] - startColor[1]) * wordProgress);
                    const b = Math.round(startColor[2] + (endColor[2] - startColor[2]) * wordProgress);

                    span.style.color = `rgb(${r}, ${g}, ${b})`;
                });
            });
        }

        // Stats counter animation
        const statNumbers = this.el.querySelectorAll(".stat-number");
        if (statNumbers.length) {
            const countedNumbers = new Set();

            window.addEventListener("scroll", () => {
                const viewportHeight = window.innerHeight;

                statNumbers.forEach((stat) => {
                    const statRect = stat.getBoundingClientRect();

                    if (statRect.top < viewportHeight && statRect.bottom > 0 && !countedNumbers.has(stat)) {
                        countedNumbers.add(stat);

                        const text = stat.textContent;
                        let finalValue;

                        if (text.includes("k")) {
                            finalValue = parseFloat(text) * 1000;
                        } else {
                            finalValue = parseInt(text, 10);
                        }

                        const startValue = 0;
                        const duration = 2000;
                        const startTime = Date.now();

                        const animate = () => {
                            const elapsed = Date.now() - startTime;
                            const progress = Math.min(elapsed / duration, 1);
                            const currentValue = Math.floor(startValue + (finalValue - startValue) * progress);

                            if (text.includes("k")) {
                                stat.textContent = (currentValue / 1000).toFixed(1) + "k";
                            } else if (text.includes("+")) {
                                stat.textContent = currentValue + "+";
                            } else {
                                stat.textContent = currentValue;
                            }

                            if (progress < 1) {
                                requestAnimationFrame(animate);
                            } else {
                                stat.textContent = text;
                            }
                        };

                        animate();
                    }
                });
            });
        }
    },
});
