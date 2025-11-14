/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { loadCSS, loadJS } from "@web/core/assets";

let owlAssetsPromise;

function ensureOwlAssets() {
    if (!owlAssetsPromise) {
        if (typeof window.$ !== "undefined" && $.fn.owlCarousel) {
            owlAssetsPromise = Promise.resolve();
        } else {
            owlAssetsPromise = Promise.all([
                loadCSS("/theme_shopping/static/src/css/owl.carousel.min.css"),
                loadCSS("/theme_shopping/static/src/css/owl.theme.default.min.css"),
                loadJS("/theme_shopping/static/src/js/owl.carousel.min.js"),
            ]);
        }
    }
    return owlAssetsPromise;
}

publicWidget.registry.TestimonialWidget = publicWidget.Widget.extend({
    selector: '.testimonial-section',
    disabledInEditableMode: false,

    events: {
        'click #add_testimonial': '_onClickAddTestimonial',
        'click #submit_testimonial': '_onClickSubmit',
    },

    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            return ensureOwlAssets();
        }).then(function() {
            return self._loadTestimonials();
        }).then(function() {
            if (user && user.userId) {
                return self._fetchUserGroup();
            }
        });
    },

    async _fetchUserGroup() {
        try {
            const result = await rpc('/fetch_user_group', { userId: user.userId });
            const addTestimonial = this.el.querySelector("#add_testimonial");
            if (addTestimonial) {
                addTestimonial.style.display = result ? "block" : "none";
            }
        } catch (error) {
            console.error("Error fetching user group:", error);
        }
    },

    async _loadTestimonials() {
        try {
            const testimonials = await rpc('/website/testimonials/fetch');
            const carousel = this.el.querySelector('#testimonial_carousel');
            if (!carousel) return;

            // Destroy existing Owl instance if needed
            if (window.$ && $(carousel).hasClass('owl-loaded')) {
                $(carousel).trigger('destroy.owl.carousel');
            }

            // Reset carousel container
            carousel.innerHTML = '';
            carousel.classList.remove('owl-loaded', 'owl-carousel');

            if (testimonials && testimonials.length) {
                testimonials.forEach(t => {
                    const item = document.createElement('div');
                    item.className = 'item st-testimonial__card';
                    item.innerHTML = `
                        <div class="st-testimonial__person--detail">
                            <div class="st-testimonial__person-img mt-1">
                                ${t.image
                                    ? `<img src="data:image/jpeg;base64,${t.image}" alt="Testimonial" class="st-auto-image"/>`
                                    : ''}
                            </div>
                            <div>
                                <p class="st-testimonial_name" style="font-size: 15pt;">${t.user_id && t.user_id[1]}</p>
                            </div>
                        </div>
                        <p class="st-testimonial__content p-3">${t.testimonial}</p>
                    `;
                    carousel.appendChild(item);
                });
                this._initCarousel(carousel);
            }
        } catch (error) {
            console.error("Error loading testimonials:", error);
        }
    },

    _initCarousel(carousel) {
        if (window.$ && $.fn.owlCarousel) {
            $(carousel).addClass('owl-carousel').owlCarousel({
                items: 1,
                loop: true,
                nav: true,
                dots: true,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause: true,
                smartSpeed: 500,
                responsive: {
                    0: { items: 1 },
                    600: { items: 1 },
                    1000: { items: 1 },
                },
            });
        }
    },

    _onClickAddTestimonial(ev) {
        ev.preventDefault();
        const form = this.el.querySelector('#testimonial_form');
        form.style.display = form.style.display === 'block' ? 'none' : 'block';
    },

    async _onClickSubmit(ev) {
        ev.preventDefault();
        const form = this.el.querySelector('#testimonial_form');
        const input = this.el.querySelector('#testimonial');
        const value = input.value.trim();

        if (!value) {
            alert("Please enter your testimonial.");
            return;
        }

        try {
            const result = await rpc("/website/testimonial/create", { testimonial: value });
            if (result.status === 'success') {
                alert("Thank you for your testimonial!");
                input.value = '';
                form.style.display = 'none';
                await this._loadTestimonials();
            } else {
                alert("Failed to submit testimonial.");
            }
        } catch (error) {
            console.error("Error submitting testimonial:", error);
            alert("An error occurred while submitting your testimonial.");
        }
    },
});


// /** @odoo-module */
// import Animation from "@website/js/content/snippets.animation";
// import { useRef } from "@odoo/owl";
// import { rpc } from "@web/core/network/rpc";
// import { user } from "@web/core/user";
// import { loadCSS, loadJS } from "@web/core/assets";

// let owlCarouselAssetsPromise;

// function ensureOwlCarouselAssets() {
//     if (!owlCarouselAssetsPromise) {
//         if (typeof window.$ !== "undefined" && $.fn.owlCarousel) {
//             owlCarouselAssetsPromise = Promise.resolve();
//         } else {
//             owlCarouselAssetsPromise = Promise.all([
//                 loadCSS("/web/static/lib/owlCarousel/css/owl.carousel.min.css"),
//                 loadCSS("/web/static/lib/owlCarousel/css/owl.theme.default.min.css"),
//                 loadJS("/web/static/lib/owlCarousel/owl.carousel.min.js"),
//             ]);
//         }
//     }
//     return owlCarouselAssetsPromise;
// }

// Animation.registry.testimonial = Animation.Class.extend({
//     selector: '.testimonial-section',
//     events: {
//         'click #add_testimonial': '_onClickAddTestimonial',
//         'click #submit_testimonial': '_onClickSubmit',
//     },

//     async start() {
//         await this._super(...arguments);
//         await ensureOwlCarouselAssets();
//         this.count = null;
//         await this._loadTestimonials();

//         if (user.userId) {
//             await this._fetchUserGroup();
//         }
//     },

//     async _fetchUserGroup() {
//         try {
//             const result = await rpc('/fetch_user_group', {
//                 userId: user.userId,
//             });
//             const addTestimonial = this.el.querySelector("#add_testimonial");
//             if (addTestimonial) {
//                 addTestimonial.style.display = result ? "block" : "none";
//             }
//         } catch (error) {
//             console.error("Error fetching user group:", error);
//         }
//     },

//     async _loadTestimonials() {
//         try {
//             const testimonials = await rpc('/website/testimonials/fetch');
//             const carouselElement = this.el.querySelector('#testimonial_carousel');

//             if ($(carouselElement).hasClass('owl-loaded')) {
//                 $(carouselElement).owlCarousel('destroy');
//             }

//             $(carouselElement).removeClass('owl-carousel owl-loaded owl-drag');

//             if (testimonials && testimonials.length > 0) {
//                 carouselElement.innerHTML = '';

//                 testimonials.forEach(testimonial => {
//                     const itemDiv = document.createElement('div');
//                     itemDiv.className = 'item st-testimonial__card';
//                     itemDiv.innerHTML = `
//                         <div class="st-testimonial__person--detail">
//                             <div class="st-testimonial__person-img mt-1">
//                                 ${testimonial.image ?
//                                     `<img src="data:image/jpeg;base64,${testimonial.image}"
//                                           alt="Testimonial Image" class="st-auto-image"/>` : ''}
//                             </div>
//                             <div>
//                                 <p class="st-testimonial_name" style="font-size: 15pt;">
//                                     ${testimonial.user_name}
//                                 </p>
//                             </div>
//                         </div>
//                         <p class="st-testimonial__content p-3">
//                             ${testimonial.testimonial}
//                         </p>
//                     `;
//                     carouselElement.appendChild(itemDiv);
//                 });

//                 this._initializeCarousel();
//             }
//         } catch (error) {
//             console.error('Error loading testimonials:', error);
//         }
//     },

//     _initializeCarousel() {
//         const carouselElement = this.el.querySelector('#testimonial_carousel');
//         $(carouselElement).addClass('owl-carousel');
//         $(carouselElement).owlCarousel({
//             items: 1,
//             loop: true,
//             margin: 0,
//             nav: true,
//             navText: ['', ''],
//             dots: true,
//             autoplay: true,
//             autoplayTimeout: 5000,
//             autoplayHoverPause: true,
//             smartSpeed: 500,
//             responsive: {
//                 0: { items: 1 },
//                 600: { items: 1 },
//                 1000: { items: 1 }
//             },
//             onInitialized: function() {
//                 $(carouselElement).trigger('refresh.owl.carousel');
//             }
//         });
//     },

//     _onClickAddTestimonial(ev) {
//         ev.preventDefault();
//         const testimonialForm = this.el.querySelector('#testimonial_form');
//         testimonialForm.style.display =
//             testimonialForm.style.display === 'none' || testimonialForm.style.display === ''
//                 ? 'block'
//                 : 'none';
//     },

//     async _onClickSubmit(ev) {
//         ev.preventDefault();
//         const testimonialForm = this.el.querySelector('#testimonial_form');
//         const testimonialInput = this.el.querySelector('#testimonial');
//         const testimonialText = testimonialInput.value.trim();

//         if (!testimonialText) {
//             alert("Please fill out the testimonial.");
//             return;
//         }

//         try {
//             const result = await rpc("/website/testimonial/create", {
//                 testimonial: testimonialText,
//             });

//             if (result.status === 'success') {
//                 alert("Thank you for your testimonial!");
//                 testimonialInput.value = '';
//                 testimonialForm.style.display = 'none';
//                 await this._loadTestimonials();
//             } else {
//                 alert("Failed to submit testimonial.");
//             }
//         } catch (error) {
//             console.error("Error submitting testimonial:", error);
//             alert("An error occurred while submitting your testimonial.");
//         }
//     },
// });
