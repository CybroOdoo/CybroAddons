/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { registry } from "@web/core/registry";

export const NavigationScroll = PublicWidget.Widget.extend({
    selector: "#wrapwrap",

    start() {
        this._super.apply(this, arguments);
        this._handleNavStyle();
        this._navbar_animation();
        this._setupScrollHandler();
        this._initializeAnimations();
        this._triggerHeroAnimation();
        this._setupPortfolioAnimations();
    },

    _setupScrollHandler() {
        this._onScroll = this._onScroll.bind(this);
        window.addEventListener('scroll', this._onScroll);
        this._setupIntersectionObserver();
    },

    _setupIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1,
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    this._triggerAnimation(target);
                    this.observer.unobserve(target);
                }
            });
        }, options);

        // Expanded list of animated elements
        const animatedElements = document.querySelectorAll(
            '.anime_video, .anime_video_right, .anime_h, .anime_card, .anime_h2, ' +
            '.anime_card2, .anime_grid2, .testimonial, .location_head, ' +
            '.location_left, .location_right, .anime_section, .anime_grid'
        );

        animatedElements.forEach(element => {
            this.observer.observe(element);
        });
    },

    _triggerAnimation(element) {
        // Comprehensive animation method covering all classes
        const animationOptions = {
            duration: 1.5,
            ease: "power2.out"
        };

        // Left sliding animations (from left)
        if (element.classList.contains('anime_video') ||
            element.classList.contains('anime_h') ||
            element.classList.contains('anime_card') ||
            element.classList.contains('anime_h2') ||
            element.classList.contains('testimonial') ||
            element.classList.contains('location_head') ||
            element.classList.contains('location_left')) {
            gsap.fromTo(element,
                { x: "-100vw", opacity: 0 },
                { x: 0, opacity: 1, ...animationOptions }
            );
        }

        // Right sliding animations (from right)
        else if (element.classList.contains('anime_video_right') ||
                 element.classList.contains('anime_card2') ||
                 element.classList.contains('anime_grid2') ||
                 element.classList.contains('location_right')) {
            gsap.fromTo(element,
                { x: "200vw", opacity: 0 },
                { x: 0, opacity: 1, ...animationOptions }
            );
        }

        // Grid and section animations
        else if (element.classList.contains('anime_grid') ||
                 element.classList.contains('anime_section')) {
            gsap.fromTo(element,
                { y: "50px", opacity: 0 },
                { y: 0, opacity: 1, duration: 1.5, ease: "power2.out" }
            );
        }
    },

     _setupPortfolioAnimations() {
        setTimeout(() => {
            // Portfolio header animation
            const portfolioHeader = document.querySelector('.project_head');
            const portfolioTitle = document.querySelector('.project_head h1');

            if (portfolioHeader && portfolioTitle) {
                // Create a timeline for more complex animations
                const tl = gsap.timeline({ defaults: { duration: 1 } });

                // Animate background
                tl.fromTo(portfolioHeader,
                    { opacity: 0, y: -50 },
                    { opacity: 1, y: 0, ease: "power2.out" }
                )
                // Animate title
                .fromTo(portfolioTitle,
                    { opacity: 0, scale: 0.5 },
                    { opacity: 1, scale: 1, ease: "back.out(1.7)" },
                    0.5 // Slight delay for staggered effect
                );
            }
        }, 100);
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