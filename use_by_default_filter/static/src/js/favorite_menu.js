/** @odoo-module **/

import { patch } from 'web.utils';
const { Component, QWeb } = owl;
const FavoriteMenu =  require('web.FavoriteMenu');

patch(FavoriteMenu.prototype, 'FavoriteMenu', {
    /**
    * Function will be executed when the checkbox is enabled/disabled from the view. 'if' condition will be executed when checkbox
    * is enabled and 'else' will be executed when disabled. 'createDefFilter' function is called to convert filter to default filter.
    *
    * @param {object} item Item object contains details of the filter such as description, id.
    */
    async onClickCheckBox(item){
        if(item.isActive == false){
            delete(item.isActive)
            item['isDefault'] = true
            this.model.dispatch('toggleFilter', item.id);
            this.model.dispatch('createDefFilter', item);
        }
        else{
            item['isDefault'] = false
            await this.model.dispatch('createDefFilter', item);
            item.isActive = false
            location.reload();
        }
    },
});
FavoriteMenu.template = "use_by_default_filter.FavoriteMenu";
FavoriteMenu.nextId = 1;
QWeb.registerComponent("FavoriteMenuInherit", FavoriteMenu);
