/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"
// Define a new widget called NavigationScroll
export const NavigationScroll = PublicWidget.Widget.extend({
    // Set the selector to the element with id 'wrapwrap', which is the main wrapper of the page
    selector: "#wrapwrap",
    // Define the events to be handled by the widget
    events: {
        'scroll': '_handleScroll',
    },
    start() {
        this._super.apply(this, arguments);
        this._handleNavStyle() // Apply styling to the navigation bar based on the current page
        this._navbar_animation()// Initialize navbar animations
        this._hero_animation()// Initialize animations for the hero section
        const actionManager = document.querySelector('.homepage');
        //Video Animation
        gsap.fromTo(
            ".anime_video",
            { x: "-100vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".anime_video",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    once: true,
                }
            }
        );
        gsap.fromTo(
            ".anime_video_right",
            { x: "200vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".anime_video_right",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    once: true,
                }
            }
        );
        //service Animation
        gsap.fromTo(
          ".anime_h",
          {
            y: "-100%", // Start position (off-screen above)
            opacity: 0, // Start with opacity 0 (fully transparent)
          },
          {
            y: 0, // End position (at original place)
            opacity: 1, // End with opacity 1 (fully visible)
            duration: 2, // Slower duration for smoother effect
            ease: "power3.out", // Smooth easing for a gradual effect
            delay: 0.5, // Optional delay for smoother timing with the cards
            scrollTrigger: {
              trigger: ".anime_h", // Trigger animation on scroll
              start: "top 50%", // Start animation when the heading reaches 50% of the viewport height
              toggleActions: "play none none none", // Play once
              scroller: actionManager,
                    once: true,
            },
          }
        );
        // Cards Animation
        gsap.from(".anime_card", {
          opacity: 0,
          y: 100, // Animates from below the initial position
          duration: 1.2, // Slightly longer duration for smoother animation
          ease: "power3.out", // Smooth easing for cards as well
          stagger: {
            each: 0.3, // Time between each card's animation (adjust as needed)
            from: "start", // Animates in DOM order (one after the other)
          },
          scrollTrigger: {
            trigger: ".anime_grid",
            start: "top 50%", // Start animation when the grid reaches 50% of the viewport height
            toggleActions: "play none none none",
            scroller: actionManager,
            once: true,// Play once
          },
        });

        //process Animation
        gsap.fromTo(
            ".anime_h2",
            { x: "-100vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".anime_h2",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        gsap.fromTo(
            ".anime_card2",
            { x: "200vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".anime_card2",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        gsap.fromTo(
            ".anime_grid2",
            { x: "200vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".anime_grid2",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        //testimonial Animation
        gsap.fromTo(
            ".testimonial",
            { x: "-100vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".testimonial",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        //location Animation
        gsap.fromTo(
            ".location_head",
            { x: "-100vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".location_head",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        gsap.fromTo(
            ".location_left",
            { x: "-100vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".location_left",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
        gsap.fromTo(
            ".location_right",
            { x: "200vw", opacity: 0 },
            {
                x: 0,
                opacity: 1,
                duration: 1.5,
                scrollTrigger: {
                    trigger: ".location_right",
                    start: "top 80%",
                    toggleActions: "play none none none",
                    scroller: actionManager,
                    invalidateOnRefresh: true,
                    once: true,
                }
            }
        );
    },
    _handleNavStyle() {
        const currentPath = window.location.pathname
        const targetNav = this.$el.find('a.nav-link')
        const logoName = this.$el.find('#theme_name')
        const toggleButton = this.$el.find('.navbar-toggler img')
        if(currentPath === "/"){
            if (targetNav.length > 0) {
                targetNav.removeClass('nav-link2');
                logoName.addClass('span1').removeClass('brandD');
            }
        }

        else {
            if (targetNav.length > 0) {
                targetNav.addClass('nav-link2');
                logoName.addClass('brandD').removeClass('span1');
                toggleButton.attr('src', '/theme_upshift/static/src/img/icons/black.svg');
            }
        }
    },
    _navbar_animation(){
        //Navbar Animation
        const timeline = gsap.timeline({ default: { duration: 1 } });
        timeline
          .from(".navigation", { y: "-100%", duration: 2, ease: "bounce" })
          .from(".nav-link", { opacity: 0, stagger: 0.5 })
          .from(
                ".navbar-brand",
                { x: "-100%", opacity: 0 },  // Start state (opacity 0)
                { x: "0%", opacity: 1, ease: "power1.in" },  // End state (opacity 1)
                "<.5"  // Overlap with previous animation
          );
    },
    _hero_animation(){
      const letters = document.querySelectorAll(".text span");
      // Animate each letter with a staggered delay
      gsap.to(letters, {
        opacity: 1, // Fade in
        y: 0, // Move from -20px to 0
        duration: 0.5, // Animation duration for each letter
        ease: "power2.out", // Easing for smooth effect
        stagger: 0.1, // Delay between each letter
      });
      gsap.registerPlugin(); // No need for ScrollTrigger

    class RevealOnLoad {
      constructor() {
        this.DOM = {
          hero: document.querySelector(".hero"),
          hero_title: document.querySelector(".hero__title"),
          hero_subtitle: document.querySelector(".hero__subtitle"),
        };
        this.tl = gsap.timeline();
        this.init();
      }
      init() {
        this.tl.add(this.heroAnimation());
      }
      heroAnimation() {
        var tl = gsap.timeline({ defaults: { duration: 1, opacity: 0 } });
        tl.from(this.DOM.hero, {
          scale: 2,
        });
        tl.from(this.DOM.hero_title, {
          y: -10,
          scale: 0.5,
        });
        tl.from(this.DOM.hero_subtitle, {
          y: 10,
          scale: 0.5,
        });

        return tl;
      }
    }
    new RevealOnLoad(); // Only animation on load

   },
    _handleScroll: function () {
        // Method to handle scroll event and change the navigation style based on scroll position
        const currentPath = window.location.pathname;

        // Handle navigation class additions
        if (this.$el.scrollTop() > 0) {
            if (currentPath === "/") {
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

