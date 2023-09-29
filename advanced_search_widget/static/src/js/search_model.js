/** @odoo-module **/
/**
 * This file is used to add a some functions to SearchModel for creating filter .
 */
import { SearchModel} from "@web/search/search_model";
import {patch} from "@web/core/utils/patch";
import {toTree} from "@advanced_search_widget/js/domain_tree"

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

    DomainDescription(tree) {
        // Returns a description for the domain to show in the search bar.
        const getFieldString = (path) => {
            if (path.includes(".")) {
                const [mainField, subField] = path.split(".");
                return `${this.searchViewFields[mainField].string} ${this.searchViewFields[subField].string}`;
            } else {
                return this.searchViewFields[path].string;
            }
        };
        let description;
        switch (tree.type) {
            case 'condition':
                description = this.FieldType(tree, getFieldString(tree.path));
                break;
            case 'connector':
                const childDescriptions = tree.children.map((childTree) =>
                    this.FieldType(childTree, getFieldString(childTree.path)));
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
