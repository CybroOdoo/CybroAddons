/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.Odometer = publicWidget.Widget.extend({
    selector: '.counter-area',
    start: function () {
        var self = this;
        const dataSet = this.el.dataset;
        console.log(dataSet)
        const counters = [
                { attr: 'expCount', title: _t('Years Experienced') },
                { attr: 'happyCount', title: _t('Happy Clients') },
                { attr: 'projectCount', title: _t('Project Completed') },
                { attr: 'activeCount', title: _t('Active Project') }
            ];
        const $row = this.$el.find('.row');
        $row.empty()
        counters.forEach(counter => {
            const value = dataSet[counter.attr] + "";
            const $counter = $(
                `<div class="col-6 col-sm-6 col-md-3 col-lg-3">
                    <div class="counter-item">
                        <h3>
                            <span class="odometer" data-count="${value}">0</span>
                        </h3>
                        <p>${counter.title}</p>
                    </div>
                </div>`
            );
            $row.append($counter);
        });


        // Initialize odometer elements
        this.$el.find('.odometer').each(function () {
            new Odometer({
                el: this,
                value: 0,
                format: 'd',  // Changed format to show numbers only
                duration: 2000  // Animation duration in milliseconds
            });
        });

        // Start animation when element is in viewport
        function animateOnScroll() {
            var elements = self.$el.find('.odometer');
            elements.each(function () {
                var element = $(this);
                var elementTop = element.offset().top;
                var elementBottom = elementTop + element.outerHeight();
                var viewportTop = $(window).scrollTop();
                var viewportBottom = viewportTop + $(window).height();
                if (elementBottom > viewportTop && elementTop < viewportBottom) {
                    var finalValue = element.data('count');
                    element.html(finalValue);
                } else {
                    element.html("00");
                }
            });
        }

        // Run on scroll and initial page load
        $(window).on('scroll', animateOnScroll);
        animateOnScroll();

        return this._super.apply(this, arguments);
    },
});
