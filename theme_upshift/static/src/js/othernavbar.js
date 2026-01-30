/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { registry } from "@web/core/registry";

export const NavigationScroll = PublicWidget.Widget.extend({
    selector: "#wrapwrap",

    start() {
        const superDef = this._super.apply(this, arguments);
        this._handleNavStyle();
        // Disabling all animations for persistent editability
        return superDef;
    },

    _setupScrollHandler() {
        this._onScroll = this._onScroll.bind(this);
        window.addEventListener('scroll', this._onScroll);
    },

    _setupIntersectionObserver() {
        // Removed card animations for troubleshooting editability
    },

    _triggerAnimation(element) {
        // Removed card animations for troubleshooting editability
    },

    _setupPortfolioAnimations() {
        // Keeping only essential header logic if needed, but currently empty for troubleshooting
    },


    _triggerHeroAnimation() {
        setTimeout(() => {
            // Letter span animation
            const letters = document.querySelectorAll(".text span");
            if (letters.length > 0) {
                gsap.to(letters, {
                    opacity: 1,
                    y: 0,
                    duration: 0.5,
                    ease: "power2.out",
                    stagger: 0.1,
                });
            }

            // Hero elements animation
            const heroElements = {
                hero: document.querySelector(".hero"),
                hero_title: document.querySelector(".hero__title"),
                hero_subtitle: document.querySelector(".hero__subtitle"),
            };

            // Verify elements exist before animating
            if (heroElements.hero && heroElements.hero_title && heroElements.hero_subtitle) {
                const tl = gsap.timeline({
                    defaults: {
                        duration: 1,
                        opacity: 0
                    }
                });

                tl.from(heroElements.hero, {
                    scale: 2
                })
                    .from(heroElements.hero_title, {
                        y: -10,
                        scale: 0.5
                    })
                    .from(heroElements.hero_subtitle, {
                        y: 10,
                        scale: 0.5
                    });
            }
        }, 100);
    },

    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        window.removeEventListener('scroll', this._onScroll);
        this._super.apply(this, arguments);
    },

    _initializeAnimations() {
        // Ensure GSAP is fully initialized
        if (window.gsap) {
            window.gsap.registerPlugin();
        }
    },

    _handleNavStyle() {
        const currentPath = window.location.pathname;
        const targetNav = this.$el.find('a.nav-link');
        const logoName = this.$el.find('#theme_name');
        const toggleButton = this.$el.find('.navbar-toggler img');

        if (currentPath === "/" || currentPath === "/home") {
            if (targetNav.length > 0) {
                targetNav.removeClass('nav-link2');
                logoName.addClass('span1').removeClass('brandD');
            }

        } else {
            if (targetNav.length > 0) {
                targetNav.addClass('nav-link2');
                logoName.addClass('brandD').removeClass('span1');
                toggleButton.attr('src', '/theme_upshift/static/src/img/icons/black.svg');
            }
        }
    },

    _navbar_animation() {
        const timeline = gsap.timeline({ defaults: { duration: 1 } });
        timeline
            .from(".navigation", { y: "-100%", duration: 2, ease: "bounce" })
            .from(".nav-link", { opacity: 0, stagger: 0.5 })
            .from(
                ".navbar-brand",
                { x: "-100%", opacity: 0 },
                { x: "0%", opacity: 1, ease: "power1.in" },
                "<.5"
            );
    },

    _onScroll() {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const currentPath = window.location.pathname;

        if (scrollTop > 0) {
            if (currentPath === "/" || currentPath === "/home") {
                this.$el.find(".navigation")[0].classList.add("scrolled");
            } else {
                this.$el.find(".navigation")[0].classList.add("scrolled2");
            }
        } else {
            this.$el.find(".navigation")[0].classList.remove("scrolled", "scrolled2");
        }
    },
});

PublicWidget.registry.NavigationScroll = NavigationScroll;