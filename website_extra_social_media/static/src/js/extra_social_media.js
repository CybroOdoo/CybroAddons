/** @odoo-module **/

/**
 * Public widget to manage visibility of social media icons
 * based on values configured in website settings.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PublicWidgetExtraSocialMedia = publicWidget.Widget.extend({
    selector: '.extra_social_media',

    /**
     * Initialize the widget and bind ORM service.
     */
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

    /**
     * Fetch configured social media values and update UI visibility.
     */
    async start() {
        await this._super(...arguments);
        try {
            const result = await this.orm.call(
                'res.config.settings',
                'get_social_media_values',
                [0]
            );
            this.toggleSocialMediaIcons(result);
        } catch (error) {
        }
    },

    /**
     * Hide social media icons if corresponding values are not configured.
     *
     * @param {Object} result - Dictionary containing social media values.
     */
    toggleSocialMediaIcons(result) {
        const socialMediaPlatforms = [
            'instagram', 'whatsapp', 'github',
            'youtube', 'google_plus', 'snapchat',
            'flickr', 'quora', 'pinterest',
            'dribbble', 'tumblr'
        ];
        socialMediaPlatforms.forEach(platform => {
            if (!result[platform]) {
                this.$el.find(`.extra_social_media_${platform}`).hide();
            }
        });
    }
});