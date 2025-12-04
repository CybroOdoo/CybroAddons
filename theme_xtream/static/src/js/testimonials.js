/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

var TestimonialWidget = publicWidget.Widget.extend({
    selector: ".testimonial_xtream",

    willStart: async function () {
        try {
            // Fetch testimonials including partner info
            const data = await rpc('/get_testimonials', {});
            // Ensure partner_id has {id, name, function} for template
            const testimonials = data?.testimonials?.map(t => ({
                ...t,
                partner_id: t.partner_id[0] ? {
                    id: t.partner_id[0],
                    name: t.partner_id[1],
                    funct: t.partner_function || '',
                } : null
            }));

            // Render template
            this.$el.html(renderToFragment('theme_xtream.s_testimonials', {
                testimonial_ids: testimonials,
            }));

        } catch (error) {
            console.error("Error loading testimonials:", error);
        }
    },

    start: function () {
        this._super(...arguments);
        const $slider = this.$el.find("#slider2");
        if ($slider.length) {
            $slider.owlCarousel({
                items: 1,
                loop: true,
                smartSpeed: 450,
                autoplay: true,
                autoplayTimeout: 2000,
                autoplayHoverPause: true,
                dots: true,
            });
        }
    },
});

publicWidget.registry.testimonial_xtream_widget = TestimonialWidget;
export default TestimonialWidget;
