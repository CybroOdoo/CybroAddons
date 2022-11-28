odoo.define('backend_theme_infinito.theme_editor', function (require) {
"use strict";

    var Widget = require('backend_theme_infinito.ThemeStudioWidget');
    var core = require('web.core');
    var ThemeEditorSidebar = require('backend_theme_infinito.theme_editor_sidebar');
    var AdvancedFeatures = require('backend_theme_infinito.AdvancedFeatures');
    var ThemeStudioMenu = require('backend_theme_infinito.ThemeStudioMenu');
    var ThemeEditor = Widget.extend({
        template: 'backend_theme_infinito.theme_editor',
        xmlDependencies: ['/backend_theme_infinito/static/src/xml/views.xml'],
        events: {
          'click .item': 'onItemClick',
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.theme = false;
            this.object = false;
            this.item = false;
            this.sidebar_view = false;
        },

        start: function () {
            this._super.apply(this, arguments);
            this.object = $($('.dash_main').firstChild);
            this.menu = new ThemeStudioMenu(this, this.action);
            this.menu.appendTo(this.$el[0]);
            this.render();
        },

        _onToggleSidebar: function () {
            this.sidebar_pos = $('.backend_theme_studio_sidebar .sidebar-here');
            if(this.sidebar) this.sidebar.destroy();
            if(!this.sidebarAdvanced){
                this.sidebarAdvanced = new AdvancedFeatures(this, 'global');
                this.sidebarAdvanced.prependTo(this.sidebar_pos);
            } else {
                this.sidebarAdvanced.$el.next().addClass('marg_main')
                this.sidebarAdvanced.destroy();
                this.sidebarAdvanced = false;
            }
        },

        onItemClick: function (ev) {
            ev.stopPropagation();
            this.sidebar_pos = $('.backend_theme_studio_sidebar .sidebar-here');
            this.object = this.$(ev.currentTarget);
            if(this.sidebarAdvanced) this.sidebarAdvanced.destroy();
            if (this.sidebar_view) {
                this.sidebar.destroy();
                this.sidebar = new ThemeEditorSidebar(this, this.object);
                this.sidebar.prependTo(this.sidebar_pos);
            } else {
                this.sidebar = new ThemeEditorSidebar(this, this.object);
                this.sidebar.prependTo(this.sidebar_pos);
            }
            this.sidebar_view = true;
        },

        render: function () {
            this.$('.items').html('');
            this.$('#view-name').html('');
            this.$('#view-para').html('');
            this.$('.colors').html('');
            var view = 'ThemeStudio.' + this.editMode
            this.$('.items').html(core.qweb.render(view));
            this.$('#view-name').html(this.editMode.charAt(0).toUpperCase() + this.editMode.slice(1).replace('_', ' '));
            let para = `Style ${this.editMode.replace('_', ' ')} the way you want using the option available.Preview will be generated here`
            this.$('#view-para').html(para);
        },

        colors: function(){
            this.$('.colors').html('');
            this.$('.items').html('');
            this.$('.colors').html(core.qweb.render('ThemeStudio.colors'))
        }

    });

    return ThemeEditor;

});