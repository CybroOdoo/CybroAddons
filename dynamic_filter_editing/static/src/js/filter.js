/** @odoo-module **/
import { Domain } from "@web/core/domain";
var Dialog = require('web.Dialog');
import { makeContext } from "@web/core/context";
import { SearchModel } from "@web/search/search_model";
import { patch } from 'web.utils';
patch(SearchModel.prototype, 'filter.CustomFilterItem', {
    _getFilterDomain(excludedFilterId) {
    // function used to get the domain of the filter
        const domain = [];
        function addCondition(fieldName, valueMap) {
            const ids = [];
            for (const [valueId, value] of valueMap) {
                if (value.checked) {
                    ids.push(valueId);
                }
            }
            if (ids.length) {
                domain.push([fieldName, "in", ids]);
            }
        }
        for (const filter of this.filters) {
            if (filter.id === excludedFilterId) {
                continue;
            }
            const { fieldName, groups, values } = filter;
            if (groups) {
                for (const group of groups.values()) {
                    addCondition(fieldName, group.values);
                }
            } else {
                addCondition(fieldName, values);
            }
        }
        return domain;
    },
    getFilterByGroup(groupId){
        // given the value of search items filter into the filter
        var filter = Object.values(this.searchItems).filter((x) => {
            return x.groupId == groupId
        })
        return filter
    }
});
