/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.AboutSection = publicWidget.Widget.extend({
    selector: '.section-about, .section-about-content, .section-our-main-service',

    events: {
        'click .read-more-toggle': '_onToggleReadMore',
    },

    start: function () {
        this.$readMoreToggles = this.$('.read-more-toggle');
        this.$additionalServices = this.$('.additional-services');
        this.$readMoreTexts = this.$('.read-more-text');

        return this._super.apply(this, arguments);
    },

    _onToggleReadMore: function (ev) {
        ev.preventDefault();

        const $toggle = $(ev.currentTarget);
        const $additionalServices = $toggle.siblings('.additional-services');
        const $readMoreText = $toggle.find('.read-more-text');

        const isHidden = $additionalServices.hasClass('d-none') || $additionalServices.css('display') === 'none';

        if (isHidden) {
            $additionalServices.removeClass('d-none');
            $additionalServices.css('display', '');
            $readMoreText.text('\u00A0\u00A0Read less\u00A0\u00A0   - \u00A0\u00A0');
        } else {
            $additionalServices.addClass('d-none');
            $readMoreText.text('\u00A0\u00A0Read more\u00A0\u00A0   +\u00A0\u00A0');
        }
    },
});

export default publicWidget.registry.AboutSection;