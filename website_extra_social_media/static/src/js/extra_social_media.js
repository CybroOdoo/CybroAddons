/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.PublicWidgetExtraSocialMedia = publicWidget.Widget.extend({
    selector: '.extra_social_media',
// Function to make social media icons visible only if value entered in that
//    of fields in configuration settings of website module.
    init() {
            this._super(...arguments);
            this.orm = this.bindService("orm");
        },
    start: function () {
        var self = this
        this.orm.call(
            'res.config.settings',
            'get_social_media_values', [0]).then(function (result){

        });
        this.orm.call('res.config.settings', 'get_social_media_values', [0]).then(function (result) {
                self.toggleSocialMediaIcons(result);
        });
        return this._super.apply(this, arguments);
    },
    toggleSocialMediaIcons: function (result) {
        const socialMediaPlatforms = [
            'facebook', 'twitter', 'linkedin', 'instagram', 'whatsapp', 'github',
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
