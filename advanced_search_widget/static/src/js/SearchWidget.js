/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { SearchDropdownItem } from "@web/search/search_dropdown_item/search_dropdown_item";
import { CustomGroupByItem } from "@web/search/group_by_menu/custom_group_by_item";
import { FACET_ICONS, GROUPABLE_TYPES } from "@web/search/utils/misc";
import { sortBy } from "@web/core/utils/arrays";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { DomainSelectorDialog } from "@web/core/domain_selector_dialog/domain_selector_dialog";
const favoriteMenuRegistry = registry.category("favoriteMenu");

export class SearchWidget extends Component {
    setup() {
        // Filter
        this.dialogService = useService("dialog");
        this.filterIcon = FACET_ICONS.filter;
        // GroupBy
        const fields = [];
        for (const [fieldName, field] of Object.entries(this.env.searchModel.searchViewFields)) {
            if (this.validateField(fieldName, field)) {
                fields.push(Object.assign({ name: fieldName }, field));
            }
        }
        this.groupByIcon = FACET_ICONS.groupBy;
        this.fields = sortBy(fields, "string");
        // Favorite
        this.favoriteIcon = FACET_ICONS.favorite;
        useBus(this.env.searchModel, "update", this.render);
    }

// Filter Menu
    get Filteritems() {
    // Get filter items for the menu.
        return this.env.searchModel.getSearchItems((searchItem) =>
            ["filter", "dateFilter"].includes(searchItem.type)
        );
    }
    onFilterSelected({ itemId, optionId }) {
    // Handle selection of a filter item.
        if (optionId) {
            this.env.searchModel.toggleDateFilter(itemId, optionId);
        } else {
            this.env.searchModel.toggleSearchItem(itemId);
        }
    }
// Add custom filter dialog
    onAddCustomFilterClick() {
        const { _context: context, resModel } = this.env.searchModel;
        this.dialogService.add(DomainSelectorDialog, {
            resModel,
            domain : "[]",
            context,
            readonly : false,
            title: _t("Add Custom Filter"),
            onSave: (domain) => this.env.searchModel.splitAndAddDomain(domain),
            isDebugMode: !!this.env.debug,
        })
    }

// GroupBy Menu
    get groupByitems() {
    // Get groupBy items for the menu.
        return this.env.searchModel.getSearchItems((searchItem) =>
            ["groupBy", "dateGroupBy"].includes(searchItem.type)
        );
    }
    onGroupBySelected({ itemId, optionId }) {
    // Handle selection of a groupBy item.
        if (optionId) {
            this.env.searchModel.toggleDateGroupBy(itemId, optionId);
        } else {
            this.env.searchModel.toggleSearchItem(itemId);
        }
    }
    onAddCustomGroup(fieldName) {
    // Create new custom group by
        this.env.searchModel.createNewGroupBy(fieldName);
    }
    get hideCustomGroupBy() {
    // Hide new custom group by
        return this.env.searchModel.hideCustomGroupBy || false;
    }
    validateField(fieldName, field) {
    // Validate if a field is suitable for groupBy
        const { sortable, store, type } = field;
        return (
            (type === "many2many" ? store : sortable) &&
            fieldName !== "id" &&
            GROUPABLE_TYPES.includes(type)
        );
    }
//  Favorite Menu
    get favoriteitems() {
    // Get favorite items for the menu.
        const favorites = this.env.searchModel.getSearchItems(
            (searchItem) => searchItem.type === "favorite"
        );
        const registryMenus = [];
        for (const item of favoriteMenuRegistry.getAll()) {
            if ("isDisplayed" in item ? item.isDisplayed(this.env) : true) {
                registryMenus.push({
                    Component: item.Component,
                    groupNumber: item.groupNumber,
                    key: item.Component.name,
                });
            }
        }
        return [...favorites, ...registryMenus];
    }
    onFavoriteSelected(itemId) {
        this.env.searchModel.toggleSearchItem(itemId);
    }
    openConfirmationDialog(itemId) {
    // Open a confirmation dialog for removing a favorite item.
        const { userId } = this.favoriteitems.find((item) => item.id === itemId);
        const dialogProps = {
            title: this.env._t("Warning"),
            body: userId
                ? this.env._t("Are you sure that you want to remove this filter?")
                : this.env._t(
                      "This filter is global and will be removed for everybody if you continue."
                  ),
            confirm: () => this.env.searchModel.deleteFavorite(itemId),
            cancel: () => {},
        };
        this.dialogService.add(ConfirmationDialog, dialogProps);
    }
}
SearchWidget.template = "SearchWidget";
SearchWidget.components = {Dropdown, CustomGroupByItem, DropdownItem:SearchDropdownItem};
