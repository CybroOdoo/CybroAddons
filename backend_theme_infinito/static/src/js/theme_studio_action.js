odoo.define('backend_theme_infinito.theme_studio_action', function (require) {
"use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var ThemeEditor = require('backend_theme_infinito.theme_editor');

    var ThemeStudioAction = AbstractAction.extend({
        init: function(parent, context, options) {
            this._super.apply(this, arguments);
            this.action = context.action;
            this.title = 'Theme Studio';
        },

        start: function() {
            this.theme_editor = new ThemeEditor(this, this.action);
            this.theme_editor.appendTo(this.$('.o_content'));
            $('header').hide();
            $('body').removeClass('dark-mode');
            $(".o_action_manager").css({
                'margin': '0',
                'transition':'all .3s linear',
                'border-radius': '0',
                'padding': '0'
            });
        },

    });

    core.action_registry.add('action_theme_studio', ThemeStudioAction);

});