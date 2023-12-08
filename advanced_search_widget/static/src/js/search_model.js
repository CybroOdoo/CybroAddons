/** @odoo-module **/
/**
 * This file is used to add a some functions to SearchModel for creating filter .
 */
import { SearchModel} from "@web/search/search_model";
import {patch} from "@web/core/utils/patch";
import {toTree} from "@advanced_search_widget/js/domain_tree"
import rpc from 'web.rpc';

patch(SearchModel.prototype, 'advanced_search_widget', {
    setup() {
        return this._super(...arguments);
    },
    FieldType(tree, description) {
        // Return a description of the domain operator string based on the operator
        if (tree.valueAST.type === 2) {
            description += ' is';
            if (tree.operator === '=' && !tree.valueAST.value) {
                description += ' not';
            }
            if (tree.operator === '!=' && tree.valueAST.value) {
                description += ' not';
            }
            description += ' set';
        } else if (tree.valueAST.type === 1) {
            if (tree.operator === 'ilike') {
                description += ' contains ' + tree.valueAST.value;
            } else if (tree.operator === 'not ilike') {
                description += ' does not contain ' + tree.valueAST.value;
            } else {
                description += ' ' + tree.operator + ' ' + tree.valueAST.value;
            }
        } else if (tree.valueAST.type === 0) {
            description += ' ' + tree.operator + ' ' + tree.valueAST.value;
        }
        return description;
    },

     async DomainDescription(tree) {
        // Returns a description for the domain to show in the search bar.
        const getFieldString = async (path) => {
            if (path.includes(".")) {
                var paths = path.split(".");
                var mainField = paths[0];
                var subFields    = paths.slice(1);
                var validTypes = ['one2many','many2one','many2many']
                if(validTypes.includes(this.searchViewFields[mainField].type)){
                    var model = this.searchViewFields[mainField].relation;
                    var firstString = this.searchViewFields[mainField].string;
                    for (const subField of subFields) {
                        const result = await rpc.query({
                            model: model,
                            method: "fields_get",
                            args: [[subField]],
                        });
                        model = result[subField].relation;
                        firstString += ` > ${result[subField].string}`;
                    }
                }
                return firstString;
            } else {
                return this.searchViewFields[path].string;
            }
        };
        let description;
        let value;
        switch (tree.type) {
            case 'condition':
                description = this.FieldType(tree, await Promise.resolve(getFieldString(tree.path)));
                break;
            case 'connector':
                const childDescriptions = tree.children.map((childTree) =>
                    this.FieldType(childTree, Promise.resolve(getFieldString(tree.path))));
                description = childDescriptions.join(" or ");
                break;
        }
        return description;
    },

    async splitAndAddDomain(domain) {
        // It will split domain based domain is branch or node and create filters
        const tree = toTree(domain);
        const trees = !tree.negate && tree.value === "&" ? tree.children : [tree];
        const promises = trees.map(async (tree) => {
            const description = await this.DomainDescription(tree);
            const preFilter = {
                description,
                domain: domain,
                invisible: true,
                type: "filter",
            };
            return preFilter;
        });
        const preFilters = await Promise.all(promises);
        for (const preFilter of preFilters) {
            this.createNewFilters([preFilter]);
        }
    }
});
