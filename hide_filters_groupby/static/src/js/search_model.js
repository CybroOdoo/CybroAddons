/** @odoo-module **/
/**
 * This module contains JavaScript code that is used to customize the behavior of the Search Model
 * in the Odoo web interface. It includes patches to remove default filter and groupby options
 * based on the global or custom settings.
 */
 import session from 'web.session';
import { SearchModel } from "@web/search/search_model";
import { SearchArchParser } from "@web/search/search_arch_parser";
import { toRaw } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
//This patch is used to remove default filter and groupby option on the basis of globally or custom
patch(SearchModel.prototype, 'hide_filters_groupby.SearchModel',{
    async load(config) {
        const { resModel } = config;
        if (!resModel) {
            throw Error(`SearchPanel config should have a "resModel" key`);
        }
        this.resModel = resModel;
        const modelId = (
                await this.env.services.orm.search("ir.model", [["model", "=", resModel]], {
                    limit: 1,
                })
            )[0];
        if (session.is_hide_filters_groupby_enabled == 'True'){
            //remove default filter and groupby options globally
            if (session.hide_filters_groupby == 'global'){
                for (var key = 0; key < Object.keys(config['context']).length; key++){
                if (Object.keys(config['context'])[key].includes('search_default')){
                     delete config['context'][Object.keys(config['context'])[key]]
                    }
                }
            } else if (session.hide_filters_groupby == 'custom'){
            //remove default filter and groupby options on custom choice
                    if (eval(session.ir_model_ids).includes(modelId)){
                        for (var key = 0; key < Object.keys(config['context']).length; key++){
                            if (Object.keys(config['context'])[key].includes('search_default')){
                             delete config['context'][Object.keys(config['context'])[key]]
                            }
                        }
                    }
            }
        }
        // used to avoid useless re computations
        this._reset();
        const { comparison, context, domain, groupBy, hideCustomGroupBy, orderBy } = config;
        this.globalComparison = comparison;
        this.globalContext = toRaw(Object.assign({}, context));
        this.globalDomain = domain || [];
        this.globalGroupBy = groupBy || [];
        this.globalOrderBy = orderBy || [];
        this.hideCustomGroupBy = hideCustomGroupBy;
        this.searchMenuTypes = new Set(config.searchMenuTypes || ["filter", "groupBy", "favorite"]);
        let { irFilters, loadIrFilters, searchViewArch, searchViewFields, searchViewId } = config;
        const loadSearchView =
            searchViewId !== undefined &&
            (!searchViewArch || !searchViewFields || (!irFilters && loadIrFilters));
        const searchViewDescription = {};
        if (loadSearchView) {
            const result = await this.viewService.loadViews(
                {
                    context: this.globalContext,
                    resModel,
                    views: [[searchViewId, "search"]],
                },
                {
                    actionId: this.env.config.actionId,
                    loadIrFilters: loadIrFilters || false,
                }
            );
            Object.assign(searchViewDescription, result.views.search);
            searchViewFields = searchViewFields || result.fields;
        }
        if (searchViewArch) {
            searchViewDescription.arch = searchViewArch;
        }
        if (irFilters) {
            searchViewDescription.irFilters = irFilters;
        }
        if (searchViewId !== undefined) {
            searchViewDescription.viewId = searchViewId;
        }
        this.searchViewArch = searchViewDescription.arch || "<search/>";
        this.searchViewFields = searchViewFields || {};
        if (searchViewDescription.irFilters) {
            this.irFilters = searchViewDescription.irFilters;
        }
        if (searchViewDescription.viewId !== undefined) {
            this.searchViewId = searchViewDescription.viewId;
        }
        if (config.state) {
            this._importState(config.state);
            this.__legacyParseSearchPanelArchAnyway(searchViewDescription, searchViewFields);
            this.domainParts = {};
            this.display = this._getDisplay(config.display);
            if (!this.searchPanelInfo.loaded) {
                return this._reloadSections();
            }
            return;
        }
        this.blockNotification = true;
        this.searchItems = {};
        this.query = [];
        this.nextId = 1;
        this.nextGroupId = 1;
        this.nextGroupNumber = 1;
        // ... to rework (API for external domain, groupBy, facet)
        this.domainParts = {}; // put in state?
        const searchDefaults = {};
        const searchPanelDefaults = {};
        for (const key in this.globalContext) {
            const defaultValue = this.globalContext[key];
            const searchDefaultMatch = /^search_default_(.*)$/.exec(key);
            if (searchDefaultMatch) {
                if (defaultValue) {
                    searchDefaults[searchDefaultMatch[1]] = defaultValue;
                }
                delete this.globalContext[key];
                continue;
            }
            const searchPanelDefaultMatch = /^searchpanel_default_(.*)$/.exec(key);
            if (searchPanelDefaultMatch) {
                searchPanelDefaults[searchPanelDefaultMatch[1]] = defaultValue;
                delete this.globalContext[key];
            }
        }
        const parser = new SearchArchParser(
            searchViewDescription,
            searchViewFields,
            searchDefaults,
            searchPanelDefaults
        );
        const { labels, preSearchItems, searchPanelInfo, sections } = parser.parse();
        this.searchPanelInfo = { ...searchPanelInfo, loaded: false, shouldReload: false };
        await Promise.all(labels.map((cb) => cb(this.orm)));
        // prepare search items (populate this.searchItems)
        for (const preGroup of preSearchItems || []) {
            this._createGroupOfSearchItems(preGroup);
        }
        this.nextGroupNumber =
            1 + Math.max(...Object.values(this.searchItems).map((i) => i.groupNumber || 0), 0);
        const dateFilters = Object.values(this.searchItems).filter(
            (searchElement) => searchElement.type === "dateFilter"
        );
        if (dateFilters.length) {
            this._createGroupOfComparisons(dateFilters);
        }
        const { dynamicFilters } = config;
        if (dynamicFilters) {
            this._createGroupOfDynamicFilters(dynamicFilters);
        }
        const defaultFavoriteId = this._createGroupOfFavorites(this.irFilters || []);
        const activateFavorite = "activateFavorite" in config ? config.activateFavorite : true;
        // activate default search items (populate this.query)
        this._activateDefaultSearchItems(activateFavorite ? defaultFavoriteId : null);
        // prepare search panel sections
        /** @type Map<number,Section> */
        this.sections = new Map(sections || []);
        this.display = this._getDisplay(config.display);
        if (this.display.searchPanel) {
            /** @type DomainListRepr */
            this.searchDomain = this._getDomain({ withSearchPanel: false });
            this.sectionsPromise = this._fetchSections(this.categories, this.filters).then(() => {
                for (const { fieldName, values } of this.filters) {
                    const filterDefaults = searchPanelDefaults[fieldName] || [];
                    for (const valueId of filterDefaults) {
                        const value = values.get(valueId);
                        if (value) {
                            value.checked = true;
                        }
                    }
                }
            });
            if (Object.keys(searchPanelDefaults).length || this._shouldWaitForData(false)) {
                await this.sectionsPromise;
            }
        }
        this.blockNotification = false;
    }
});
