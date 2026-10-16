import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { ShoppingCarousel } from '@theme_shopping/js/carousel';

class Testimonial extends ShoppingCarousel {
    static selector = '.testimonial-section';
    dynamicContent = {
        '#add_testimonial': { 't-on-click.prevent': this.toggleForm },
        '#submit_testimonial': { 't-on-click.prevent': this.submit },
    };

    async willStart() {
        const [testimonials, allowed] = await this.waitFor(Promise.all([
            rpc('/website/testimonials/fetch', {}),
            rpc('/fetch_user_group', {}),
        ]));
        const button = this.el.querySelector('#add_testimonial');
        if (button) button.style.display = allowed ? 'block' : 'none';
        const carousel = this.el.querySelector('#testimonial_carousel');
        if (carousel) {
            const originalChildren = [...carousel.childNodes];
            this.registerCleanup(() => carousel.replaceChildren(...originalChildren));
        }
        this.renderTestimonials(testimonials);
    }

    start() {
        this.setupCarousel(this.el.querySelector('#testimonial_carousel'), true);
    }

    renderTestimonials(testimonials) {
        const carousel = this.el.querySelector('#testimonial_carousel');
        if (!carousel) return;
        carousel.replaceChildren();
        for (const testimonial of testimonials) {
            const item = document.createElement('div');
            item.className = 'item st-testimonial__card';
            const name = document.createElement('p');
            name.className = 'st-testimonial_name';
            name.textContent = testimonial.user_id?.[1] || '';
            const content = document.createElement('p');
            content.className = 'st-testimonial__content p-3';
            content.textContent = testimonial.testimonial;
            const imageContent = testimonial.image?.content;
            if (imageContent) {
                const image = document.createElement('img');
                image.className = 'st-auto-image';
                image.alt = '';
                image.src = `data:image/jpeg;base64,${imageContent}`;
                const wrapper = document.createElement('div');
                wrapper.className = 'st-testimonial__person-img mt-1';
                wrapper.append(image);
                item.append(wrapper);
            }
            item.append(name, content);
            carousel.append(item);
        }
    }

    toggleForm() {
        const form = this.el.querySelector('#testimonial_form');
        form.style.display = form.style.display === 'block' ? 'none' : 'block';
    }

    async submit(ev) {
        const input = this.el.querySelector('#testimonial');
        const testimonial = input.value.trim();

        if (!testimonial) {
            this.services.notification.add('Please enter your testimonial.', {
                type: 'warning',
            });
            return;
        }

        const button = ev.currentTarget;
        button.disabled = true;
        try {
            const result = await this.waitFor(
                rpc('/website/testimonial/create', { testimonial })
            );

            if (result?.status !== 'success') {
                this.services.notification.add('Failed to submit testimonial.', {
                    type: 'danger',
                });
                return;
            }

            input.value = '';
            this.el.querySelector('#testimonial_form').style.display = 'none';

            const testimonials = await this.waitFor(
                rpc('/website/testimonials/fetch', {})
            );
            this.renderTestimonials(testimonials);

            this.setupCarousel(this.el.querySelector('#testimonial_carousel'), true);

            this.services.notification.add('Thank you for your testimonial!', {
                type: 'success',
            });
        } catch (error) {
            console.error('Error submitting testimonial:', error);
            this.services.notification.add(
                'An error occurred while submitting your testimonial.',
                { type: 'danger' }
            );
        } finally {
            button.disabled = false;
        }
    }
}

registry.category('public.interactions').add('theme_shopping.testimonial', Testimonial);