/** @odoo-module **/

/**
 * This widget dynamically displays social media icons
 * based on the values configured in website settings.
 */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PublicWidgetExtraSocialMedia = publicWidget.Widget.extend({
    selector: '.extra_social_media',
    // Show social media icons only if configured in website settings
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    start: function () {
        this.orm.call('res.config.settings', 'get_social_media_values', [0]).then((result) => {
            this.toggleSocialMediaIcons(result);
        });
        return this._super.apply(this, arguments);
    },
    toggleSocialMediaIcons: function (result) {
        const socialMediaPlatforms = [
            'instagram', 'whatsapp', 'github',
            'youtube', 'google_plus', 'snapchat', 'flickr', 'quora', 'pinterest',
            'dribble', 'tumblr'
        ];
        socialMediaPlatforms.forEach(platform => {
            if (!result[platform]) {
                this.$el.find(`.extra_social_media_${platform}`).hide();
            }
        });
    }
});
