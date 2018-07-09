odoo.define('news_letter_name.massmailextend', function (require) {
"use strict";
var ajax = require('web.ajax');
var utils = require('web.utils');
var animation = require('web_editor.snippets.animation');
require('web_editor.base');
require('mass_mailing.website_integration');
//updated onclick function to feed the name from news letter subscribe
animation.registry.subscribe.include({
    on_click: function () {
        var self = this;
        var $email = this.$target.find(".js_subscribe_email:visible");
        var $name = this.$target.find(".js_subscribe_name:visible");

        if ($email.length && !$email.val().match(/.+@.+/)) {
            this.$target.addClass('has-error');
            return false;
        }
        this.$target.removeClass('has-error');
        ajax.jsonRpc('/website_mass_mailing/subscribe', 'call', {
            'list_id': this.$target.data('list-id'),
            'email': $email.length ? $email.val() : false,
            'name': $name.length ? $name.val() : false,
        }).then(function (subscribe) {
            self.$target.find(".js_subscribe_email, .input-group-btn").addClass("hidden");
            self.$target.find(".js_subscribe_name, .input-group-btn").addClass("hidden");
            self.$target.find(".alert").removeClass("hidden");
            self.$target.find('input.js_subscribe_email').attr("disabled", subscribe ? "disabled" : false);
            self.$target.find('input.js_subscribe_name').attr("disabled", subscribe ? "disabled" : false);
            self.$target.attr("data-subscribe", subscribe ? 'on' : 'off');
        });
    },

});

});