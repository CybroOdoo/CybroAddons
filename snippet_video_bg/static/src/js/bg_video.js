odoo.define('snippet_video_bg.wrapwrap_bg_video', function (require) {
    'use strict';

    var Dialog = require("web.Dialog");
    var core = require('web.core');
    var Widget = require('web.Widget');
//    var session = require('web.session');
    var base = require('web_editor.base');
    var wUtils = require('website.utils');
    var WebsiteNewMenu = require('website.newMenu');
    var website = require('website.website');

    var qweb = core.qweb;
    var _t = core._t;
    base.url_translations = '/website/translations';

    WebsiteNewMenu.include({
    	
        actions: _.extend({}, WebsiteNewMenu.prototype.actions || {}, {
        	new_bg_video_id: '_NewBgVideo',
        }),
        
        //----------------------------------------------------------------------
        // Actions
        //----------------------------------------------------------------------        
        
        /**
         * Asks the video url for new video background
         *
         * @private
         */        
        _NewBgVideo: function() {
        	var self = this;
        	wUtils.prompt({
                id: "bg_video_id",
                window_title: _t("Add a YouTube Video Id here"),
                input: "Video ID",
            }).then(function (id) {
//                website.form('/set_video_id', 'POST', {
//                    id: id
//                });
                self._rpc({
                    route: '/set_video_id',
                    params: {
                    	id: id,
                    },
                }).then(function (url) {
                    window.location.href = url;
                });                
            });
        },
    });
});

odoo.define('snippet_video_bg.wrapwrap_bg_video_load', function (require) {
    'use strict';
    var Dialog = require("web.Dialog");
    var core = require('web.core');
    var Widget = require('web.Widget');
    var session = require('web.session');
    var base = require('web_editor.base');
    var Model = require('web.Model');

    var qweb = core.qweb;
    var _t = core._t;
    base.url_translations = '/website/translations';

    $('document').ready(function() {

        session.rpc("/get_video_id", {})
            .done(function(res) {
                var options = {
                    videoId: res.video_id || false,
                    start: 0,
                    mute: true,
                };
                $('#wrapwrap').tubular(options);
            });

    });

});
