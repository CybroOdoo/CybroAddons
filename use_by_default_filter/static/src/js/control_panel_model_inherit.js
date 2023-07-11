odoo.define('use_by_default_filter.control_panel_model_inherit', function (require) {
'use strict';

    const ControlPanelModelExtension = require('web/static/src/js/control_panel/control_panel_model_extension.js')
    const { patch } = require('web.utils');
    const { Component, QWeb } = owl;
    const components = {
        ControlPanelModelExtension: require('web/static/src/js/control_panel/control_panel_model_extension.js'),
    };

    patch(components.ControlPanelModelExtension, 'use_by_default_filter.control_panel_model_inherit', {
        /**
        * Default filter is created when this function is called in which the details of the filter is available in the parameter item.
        *
        * @param {object} item Item object contains details of the filter such as description, id.
        */
        async createDefFilter(item) {
            const preFavorite = await this._saveQuery(item);
            this.clearQuery();
            const filter = Object.assign(preFavorite, {
                groupId: item.groupId,
                id: item.id,
            });
            this.state.filters[item.id] = filter;
            this.state.query.push({ groupId: item.groupId, filterId: item.id });
            this.state.groupId++;
            this.state.filterId++;
        },
    });
});
