odoo.define('use_by_default_filter.dropdown_menu_item_inherit', function (require) {
'use strict';

    const DropdownMenuItem = require('web.DropdownMenuItem')
    const { patch } = require('web.utils');
    const { Component, QWeb } = owl;
    const components = {
        DropdownMenuItem: require('web.DropdownMenuItem'),
    };
    patch(components.DropdownMenuItem, 'use_by_default_filter.dropdown_menu_item_inherit', {
        /**
        * Function will be executed when the checkbox is enabled/disabled from the view. 'if' condition will be executed when checkbox
        * is enabled and 'else' will be executed when disabled. 'createDefFilter' function is called to convert filter to default filter.
        *
        * @param {object} props Props object contains details of the filter such as description, id.
        */
        async onClickCheckBox(props) {
            if(props.isActive == false){
                delete(props.isActive)
                props['isDefault'] = true
                this.env.searchModel.dispatch('toggleFilter', props.id);
                this.env.searchModel.dispatch('createDefFilter', props);
            }
            else{
                delete(props.isActive)
                props['isDefault'] = false
                await this.env.searchModel.dispatch('createDefFilter', props);
                await this.env.searchModel.dispatch('deactivateGroup', props.groupId);
                location.reload();
            }
        },
    });
    DropdownMenuItem.template = 'use_by_default_filter.DropdownMenuItem';
    return DropdownMenuItem;
});
