/** @odoo-module **/
//Extend the public widget
var rpc = require('web.rpc');
var publicWidget = require('web.public.widget');
publicWidget.registry.PublicWidgetExtraSocialMedia = publicWidget.Widget.extend({
    selector: '.extra_social_media',
// Function to make social media icons visible only if value entered in that
//    of fields in configuration settings of website module.
    start: function () {
        var self = this
        rpc.query({
            model: 'res.config.settings',
            method: 'get_social_media_values',
            args: [0],
        }).then(function (result){
            if (result['facebook'] == false){
                self.$el.find(".extra_social_media_facebook").hide();
            }
            if (result['twitter'] == false){
                self.$el.find(".extra_social_media_twitter").hide();
            }
            if (result['linkedin'] == false){
                self.$el.find(".extra_social_media_linkedin").hide();
            }
            if (result['instagram'] == false){
               self.$el.find(".extra_social_media_instagram").hide();
            }
            if (result['whatsapp'] == false){
                self.$el.find(".extra_social_media_whatsapp").hide();
            }
            if (result['github'] == false){
                self.$el.find(".extra_social_media_github").hide();
            }
            if (result['youtube'] == false){
                self.$el.find(".extra_social_media_youtube").hide();
            }
            if (result['google_plus'] == false){
                self.$el.find(".extra_social_media_google_plus").hide();
            }
            if (result['snapchat'] == false){
                self.$el.find(".extra_social_media_snapchat").hide();
            }
            if (result['flickr'] == false){
                self.$el.find(".extra_social_media_flickr").hide();
            }
            if (result['quora'] == false){
                self.$el.find(".extra_social_media_quora").hide();
            }
            if (result['pinterest'] == false){
                self.$el.find(".extra_social_media_pinterest").hide();
            }
            if (result['dribble'] == false){
                self.$el.find(".extra_social_media_dribble").hide();
            }
            if (result['tumblr'] == false){
                self.$el.find(".extra_social_media_tumblr").hide();
            }
        });
    },
});
    var PublicWidgetExtraSocialMedia = new publicWidget.registry.PublicWidgetExtraSocialMedia(this);
    PublicWidgetExtraSocialMedia.appendTo($(".extra_social_media"));
    return publicWidget.registry.PublicWidgetExtraSocialMedia;
