odoo.define('snippet_video_bg.wrapwrap_bg_video', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var Dialog = require("web.Dialog");
    var core = require('web.core');
    var Widget = require('web.Widget');
//    var session = require('web.session');
    var base = require('web_editor.base');
    var contentMenu = require('website.contentMenu');
    var website = require('website.website');

    var qweb = core.qweb;
    var _t = core._t;
    base.url_translations = '/website/translations';

    contentMenu.TopBar.include({
        new_bg_video_id: function() {
            website.prompt({
                id: "bg_video_id",
                window_title: _t("Add a YouTube Video Id here"),
                input: "Video ID",
            }).then(function (id) {
                website.form('/set_video_id', 'POST', {
                    id: id
                });
            });
        },
    });
});

odoo.define('snippet_video_bg.wrapwrap_bg_video_load', function (require) {
    'use strict';
    var ajax = require('web.ajax');
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
