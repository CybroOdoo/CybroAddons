odoo.define('backend_theme_infinito.ThemeStudioWidget', function (require) {
"use strict";

    var Widget = require('web.Widget');

    var ThemeStudioWidget = Widget.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.localStorage = window.localStorage;
            this.loadData();
        },

        loadData: function () {
            this.editMode = this.localStorage.getItem('editMode') || 'tree';
            this.sidebar = JSON.parse(this.localStorage.getItem('sidebar')) || false;
            this.data = JSON.parse(this.localStorage.getItem('data')) || {};
            this.tool = JSON.parse(this.localStorage.getItem('tool')) || false;
        },

        saveData: function () {
            this.localStorage.setItem('editMode', this.editMode);
        },
    });

    return ThemeStudioWidget;

});