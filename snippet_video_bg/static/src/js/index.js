odoo.define('snippet_video_bg.wrapwrap_bg_video', function (require) {
    'use strict';
    var Model = require('web.Model');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var base = require('web_editor.base');
    var web_editor = require('web_editor.editor');
    var options = require('web_editor.snippets.options');
    var website = require('website.website');
    var contentMenu = require('website.contentMenu');
    var _t = core._t;

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
    $('document').ready(function() {
        var model = new Model('ir.config_parameter');
        model.call('get_param', ['video_id']).then(function(video_id){
        var options = {
            videoId: video_id || false,
            start: 0,
            mute: true,
        };
        $('#wrapwrap').tubular(options);
        });
    });
});;