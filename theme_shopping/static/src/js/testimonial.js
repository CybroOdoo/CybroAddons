/** @odoo-module */
import Animation from "@website/js/content/snippets.animation";
import { useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

Animation.registry.testimonial = Animation.Class.extend({
    selector: '.testimonial-section',
    events: {
        'click #add_testimonial': '_onClickAddTestimonial',
        'click #submit_testimonial': '_onClickSubmit',
    },

    async start() {
        await this._super(...arguments);
        this.count = null;
        await this._loadTestimonials();

        if (user.userId) {
            await this._fetchUserGroup();
        }
    },

    async _fetchUserGroup() {
        try {
            const result = await rpc('/fetch_user_group', {
                userId: user.userId,
            });
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
            const carouselElement = this.el.querySelector('#testimonial_carousel');

            if ($(carouselElement).hasClass('owl-loaded')) {
                $(carouselElement).owlCarousel('destroy');
            }

            $(carouselElement).removeClass('owl-carousel owl-loaded owl-drag');

            if (testimonials && testimonials.length > 0) {
                carouselElement.innerHTML = '';

                testimonials.forEach(testimonial => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'item st-testimonial__card';
                    itemDiv.innerHTML = `
                        <div class="st-testimonial__person--detail">
                            <div class="st-testimonial__person-img mt-1">
                                ${testimonial.image ?
                                    `<img src="data:image/jpeg;base64,${testimonial.image}"
                                          alt="Testimonial Image" class="st-auto-image"/>` : ''}
                            </div>
                            <div>
                                <p class="st-testimonial_name" style="font-size: 15pt;">
                                    ${testimonial.user_name}
                                </p>
                            </div>
                        </div>
                        <p class="st-testimonial__content p-3">
                            ${testimonial.testimonial}
                        </p>
                    `;
                    carouselElement.appendChild(itemDiv);
                });

                this._initializeCarousel();
            }
        } catch (error) {
            console.error('Error loading testimonials:', error);
        }
    },

    _initializeCarousel() {
        const carouselElement = this.el.querySelector('#testimonial_carousel');
        $(carouselElement).addClass('owl-carousel');
        $(carouselElement).owlCarousel({
            items: 1,
            loop: true,
            margin: 0,
            nav: true,
            navText: ['', ''],
            dots: true,
            autoplay: true,
            autoplayTimeout: 5000,
            autoplayHoverPause: true,
            smartSpeed: 500,
            responsive: {
                0: { items: 1 },
                600: { items: 1 },
                1000: { items: 1 }
            },
            onInitialized: function() {
                $(carouselElement).trigger('refresh.owl.carousel');
            }
        });
    },

    _onClickAddTestimonial(ev) {
        ev.preventDefault();
        const testimonialForm = this.el.querySelector('#testimonial_form');
        testimonialForm.style.display =
            testimonialForm.style.display === 'none' || testimonialForm.style.display === ''
                ? 'block'
                : 'none';
    },

    async _onClickSubmit(ev) {
        ev.preventDefault();
        const testimonialForm = this.el.querySelector('#testimonial_form');
        const testimonialInput = this.el.querySelector('#testimonial');
        const testimonialText = testimonialInput.value.trim();

        if (!testimonialText) {
            alert("Please fill out the testimonial.");
            return;
        }

        try {
            const result = await rpc("/website/testimonial/create", {
                testimonial: testimonialText,
            });

            if (result.status === 'success') {
                alert("Thank you for your testimonial!");
                testimonialInput.value = '';
                testimonialForm.style.display = 'none';
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
