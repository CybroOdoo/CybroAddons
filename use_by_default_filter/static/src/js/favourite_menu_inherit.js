/** @odoo-module **/

import { FavoriteMenu } from '@web/search/favorite_menu/favorite_menu';
import { SearchModel } from '@web/search/search_model';
import { patch } from "@web/core/utils/patch";

patch(FavoriteMenu.prototype, 'FavoriteMenu', {
    /**
    * Function will be executed when the checkbox is enabled/disabled from the view. 'if' condition will be executed when checkbox
    * is enabled and 'else' will be executed when disabled. 'newFavouriteCreation' function is called to convert filter to default filter (function in web module).
    *
    * @param {object} item Item object contains details of the filter such as description, id.
    */
    async onClickCheckBox(item){
        if(item.isActive == false){
            await this.env.searchModel.toggleSearchItem(item.id)
            this.newFavouriteCreation({'description': item.description, 'isDefault': true,'isShared': false}, item);
        }
        else{
            await this.newFavouriteCreation({'description': item.description, 'isDefault': false,'isShared': false}, item)
            await this.env.searchModel.deactivateGroup(item.groupId);
        }
    },
    /**
    * Default filter is created when this function is called in which the details of the filter is available in the parameters params and item.
    *
    * @param {object} params Params object contains details of the filter to create a new filter.
    * @param {object} item Item object contains details of the filter such as description, id to make it default filter.
    */
    async newFavouriteCreation(params, item){
        var self = this.env.searchModel;
        const { preFavorite, irFilter } = self._getIrFilterDescription(params);
        const serverSideId = await self.orm.call("ir.filters", "create_or_replace", [irFilter]);
        self.env.bus.trigger("CLEAR-CACHES");

        // before the filter cache was cleared!
        self.blockNotification = true;
        self.clearQuery();
        const favorite = {
            ...preFavorite,
            type: "favorite",
            id: item.id,
            groupId: item.groupId,
            groupNumber: item.groupNumber,
            removable: true,
            serverSideId,
        };
        self.searchItems[item.id] = favorite;
        self.query.push({ searchItemId: item.id });
        self.nextGroupId++;
        self.nextId++;
        self.blockNotification = false;
        self._notify();
    }
});
