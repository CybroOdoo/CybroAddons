odoo.define('backend_theme_infinito.ThemeStudioMenu', function (require) {
"use strict";

    var core = require('web.core');
    var Widget = require('backend_theme_infinito.ThemeStudioWidget');
    var ajax = require('web.ajax');

    var ThemeStudioMenu = Widget.extend({
        template: 'ThemeStudioMenu',
        events: {
            'click .backend_theme_studio_close': '_onThemeStudioClose',
            'click .theme_studio_toggle_sidebar': '_onThemeStudioToggleSidebar',
            'click .dropdown-item': '_onButtonClick',
            'click .reset_to_default': '_onResetClick',
        },
        init: function (parent, action) {
            this._super(this, arguments);
            this.action = action;
            this.parent = parent;
            this.editMode = parent.editMode;
            this.menus = [{
                name: 'Views',
                children: [{
                    'name': 'Tree/List',
                    'selector': 'tree',
                },
                {
                    'name': 'Form',
                    'selector': 'form',
                },
                {
                    'name': 'Kanban',
                    'selector': 'kanban',
                },
                {
                    'name': 'Control Panel',
                    'selector': 'control_panel',
                }],
            }, {
                name: 'UI Elements',
                children: [{
                   'name': 'Button',
                   'selector': 'button',
                },
               {
                  'name': 'Progress Bar',
                  'selector': 'progress_bar',
               },
               {
                  'name': 'Tab',
                  'selector': 'tab',
               },
                {
                   'name': 'Input',
                   'selector': 'input',
                },
                {
                   'name': 'Search',
                   'selector': 'search',
                },
                {
                   'name': 'Misc',
                   'selector': 'misc',
                },],
            }
        ];
        },

        _onThemeStudioClose: function (ev) {
            ev.preventDefault();
            window.location.href = '/web'
        },

        _onThemeStudioToggleSidebar: function (ev) {
            ev.currentTarget.classList.toggle('open');
            ev.preventDefault();
            this.parent._onToggleSidebar();
        },

        _onButtonClick: function (ev) {
            ev.preventDefault();
            var mode = ev.currentTarget.id;
            if(mode){
                this.parent.editMode = mode;
                this.parent.render();
                this.editMode = mode;
                var sidebar = this.parent.sidebar;
                if (sidebar) {
                    sidebar._Close();
                    sidebar.destroy();
                }
                this.saveData();
            } else {
                var mode = ev.currentTarget.dataset.other;
                this.parent.colors();
            }
        },

        _onResetClick: async function(ev){
            await ajax.jsonRpc('/theme_studio/reset_to_default', 'call', {});
            await this.setAssets();
            location.reload();
        },
        setAssets: function(){
            location.search = "?debug=assets";
        },

        saveData: function () {
            this._super.apply(this, arguments);
            this.localStorage.setItem('editMode', this.editMode);
        },
    });

    return ThemeStudioMenu;
});