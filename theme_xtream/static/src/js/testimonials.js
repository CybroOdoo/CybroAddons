/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TestimonialWidget extends Interaction {
    static selector = ".testimonial_xtream:not(.xtream_testimonial_content)";

    async willStart() {
        try {
            const data = await this.waitFor(rpc("/get_testimonials", {}));
            this.testimonials = (data.testimonials || []).map((testimonial) => ({
                ...testimonial,
                partner_id: testimonial.partner_id ? {
                    id: testimonial.partner_id[0],
                    name: testimonial.partner_id[1],
                    funct: testimonial.partner_function || "",
                } : null,
            }));
        } catch (error) {
            console.error("Error loading testimonials:", error);
        }
    }

    start() {
        if (!this.testimonials) {
            return;
        }
        this.removeChildren(this.el);
        this.renderAt("theme_xtream.s_testimonials", { testimonial_ids: this.testimonials });
        this.$slider = window.jQuery(this.el).find("#slider2");
        if (this.$slider.length) {
            this.$slider.owlCarousel({
                items: 1,
                loop: true,
                smartSpeed: 450,
                autoplay: true,
                autoplayTimeout: 2000,
                autoplayHoverPause: true,
                dots: true,
            });
        }
    }

    destroy() {
        this.$slider?.trigger("destroy.owl.carousel");
    }
}

registry.category("public.interactions").add("theme_xtream.testimonials", TestimonialWidget);
export default TestimonialWidget;
