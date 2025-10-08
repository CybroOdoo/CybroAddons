/** @odoo-module **/
import { SearchBar } from "@web/search/search_bar/search_bar";
import CustomFilterItem from "web.CustomFilterItem";
import { patch } from "@web/core/utils/patch";
const { useModel } = require('web.Model');
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { DomainSelector } from "@web/core/domain_selector/domain_selector";
import { DomainSelectorDialog } from "@web/core/domain_selector_dialog/domain_selector_dialog";
import { Component, useState } from "@odoo/owl";
import { _lt } from "@web/core/l10n/translation";
import { parseExpr } from "@web/core/py_js/py";

const FIELD_TYPES = {
    boolean: "boolean",
    char: "char",
    date: "date",
    datetime: "datetime",
    float: "number",
    id: "id",
    integer: "number",
    html: "char",
    many2many: "char",
    many2one: "char",
    monetary: "number",
    one2many: "char",
    text: "char",
    selection: "selection",
};
// FilterMenu parameters
const FIELD_OPERATORS = {
    boolean: [
        { symbol: "=", description: _lt("is Yes"), value: true },
        { symbol: "!=", description: _lt("is No"), value: true },
    ],
    char: [
        { symbol: "ilike", description: _lt("contains") },
        { symbol: "not ilike", description: _lt("doesn't contain") },
        { symbol: "=", description: _lt("is equal to") },
        { symbol: "!=", description: _lt("is not equal to") },
        { symbol: "!=", description: _lt("is set"), value: false },
        { symbol: "=", description: _lt("is not set"), value: false },
    ],
    date: [
        { symbol: "=", description: _lt("is equal to") },
        { symbol: "!=", description: _lt("is not equal to") },
        { symbol: ">", description: _lt("is after") },
        { symbol: "<", description: _lt("is before") },
        { symbol: ">=", description: _lt("is after or equal to") },
        { symbol: "<=", description: _lt("is before or equal to") },
        { symbol: "between", description: _lt("is between") },
        { symbol: "!=", description: _lt("is set"), value: false },
        { symbol: "=", description: _lt("is not set"), value: false },
    ],
    datetime: [
        { symbol: "between", description: _lt("is between") },
        { symbol: "=", description: _lt("is equal to") },
        { symbol: "!=", description: _lt("is not equal to") },
        { symbol: ">", description: _lt("is after") },
        { symbol: "<", description: _lt("is before") },
        { symbol: ">=", description: _lt("is after or equal to") },
        { symbol: "<=", description: _lt("is before or equal to") },
        { symbol: "!=", description: _lt("is set"), value: false },
        { symbol: "=", description: _lt("is not set"), value: false },
    ],
    id: [{ symbol: "=", description: _lt("is") }],
    number: [
        { symbol: "=", description: _lt("is equal to") },
        { symbol: "!=", description: _lt("is not equal to") },
        { symbol: ">", description: _lt("greater than") },
        { symbol: "<", description: _lt("less than") },
        { symbol: ">=", description: _lt("greater than or equal to") },
        { symbol: "<=", description: _lt("less than or equal to") },
        { symbol: "!=", description: _lt("is set"), value: false },
        { symbol: "=", description: _lt("is not set"), value: false },
    ],
    selection: [
        { symbol: "=", description: _lt("is") },
        { symbol: "!=", description: _lt("is not") },
        { symbol: "!=", description: _lt("is set"), value: false },
        { symbol: "=", description: _lt("is not set"), value: false },
    ],
};

patch(SearchBar.prototype, "dynamic_filter_editing", {
    // patch the search bar and parameters to the facet value also given the irFilter domain as domain
    setup(){
        this._super();
        this.dialogService = useService('dialog')
    },
    onFacetEdit(facet) {
        var params = {
            description: 'Combination',
            isDefault: false,
            isShared: false,
        }
        const { preFavorite, irFilter } = this.env.searchModel._getIrFilterDescription(params);
        var domain = irFilter.domain
        this.dialogService.add(CustomFilterDialog, {
            className: 'bg',
            resModel: this.env.searchModel.resModel,
            onApplyFilter: this.onApplyFilter.bind(this),
            domain
        });
    },
    onApplyFilter(domain, dialog){
        // Filtering the values based on the domain, description, fields ect on the onApplyFilter function
        var description = []
        var ops = []
        const fields = this.env.searchModel.searchViewFields
        var cdomain = parseExpr(domain)
        cdomain = cdomain.value;
        cdomain.forEach((dom) => {
            if(dom.type === 10){
                const field = fields[dom.value[0].value];
                const genericType = FIELD_TYPES[field.type]
                const operator = FIELD_OPERATORS[genericType][dom.value[1].value]
                const operator_string = operator ? operator.description.toString() : dom.value[1].value
                const value = typeof dom.value[2].value !== 'object' ? dom.value[2].value : dom.value[2].value.map((val) => val.value)
                description.push(`${field.string} ${operator_string} ${value}`)
            } else {
                if(dom.value === '&'){
                    ops.push('and')
                } else if (dom.value === '|'){
                    ops.push('or')
                }
            }
        })
        var description_string = ''
        for(var i = 0; i < description.length; i++){
            description_string += description[i]
            try{
                description_string += ` ${ops[i]} `
            }
            catch {
            }
        }
        const preFilter = {
            type: "filter",
            domain,
            description
        };
        this.env.searchModel.facets.forEach(element => {
            this.env.searchModel.deactivateGroup(element.groupId)
        })
        this.env.searchModel.createNewFilters([preFilter])
        dialog.props.close()
    },
});

class CustomFilterDialog extends Component {
    //super the set up and given the domain as value
    setup(){
        super.setup();
        this.state = useState({
            value: this.props.domain
        })
    }
    get domainSelectorProps() {
    // updated the value
        return {
            className: this.props.className,
            resModel: this.props.resModel,
            isDebugMode: true,
            readonly: false,
            value: this.state.value,
            update: (value) => {
                this.state.value = value;
            },
        };
    }
}
CustomFilterDialog.template = 'CustomFilterDialog'
CustomFilterDialog.components = {
    Dialog, DomainSelector
}
