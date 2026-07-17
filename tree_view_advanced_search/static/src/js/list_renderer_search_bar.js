/** @odoo-module */
import { ListRenderer } from "@web/views/list/list_renderer";
import { FileUploadListRenderer } from "@account/views/file_upload_list/file_upload_list_renderer";
import { AccountMoveListRenderer } from "@account/views/account_move_list/account_move_list_renderer";
import { SaleListRenderer } from "@sale/views/sale_onboarding_list/sale_onboarding_list_renderer";
import { PurchaseDashBoardRenderer } from "@purchase/views/purchase_listview";
import { patch } from "@web/core/utils/patch";
import { DateRange } from "./components/date_range";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        Object.assign(this.state, {
            searchTags: {}, 
            selectedItems: {}, // fieldName -> [values]
        });
        this.dateDomains = {};
    },

    _onKeyPress(ev, name) {
        if (ev.key === "Enter" && ev.currentTarget.value.trim() !== '') {
            this.addTag(ev.currentTarget.value.trim(), name);
            ev.currentTarget.value = '';
        }
    },

    addTag(tagText, name) {
        if (!this.state.searchTags[name]) {
            this.state.searchTags[name] = [];
        }
        if (!this.state.searchTags[name].includes(tagText)) {
            this.state.searchTags[name].push(tagText);
            this._updateSearchModel();
        }
    },

    _onClick_search(ev, name) {
        const input = ev.target.previousElementSibling;
        if (input && input.value.trim() !== '') {
            this.addTag(input.value.trim(), name);
            input.value = '';
        }
    },

    _updateSearchModel() {
        let fullDomain = [];
        
        // Add text search tags
        for (const [fieldName, tags] of Object.entries(this.state.searchTags)) {
            if (tags.length === 0) continue;
            const fieldDomain = [];
            const field = this.props.list.fields[fieldName];
            const operator = (field && ['integer', 'float', 'monetary'].includes(field.type)) ? '=' : 'ilike';
            if (tags.length > 1) {
                for (let i = 0; i < tags.length - 1; i++) fieldDomain.push('|');
                tags.forEach(tag => fieldDomain.push([fieldName, operator, tag]));
            } else {
                fieldDomain.push([fieldName, operator, tags[0]]);
            }
            fullDomain = fullDomain.length > 0 ? ['&', ...fullDomain, ...fieldDomain] : fieldDomain;
        }

        // Add multi-selection filters
        for (const [fieldName, values] of Object.entries(this.state.selectedItems)) {
            if (values.length === 0) continue;
            const selDomain = [];
            if (values.length > 1) {
                for (let i = 0; i < values.length - 1; i++) selDomain.push('|');
                values.forEach(v => selDomain.push([fieldName, '=', v]));
            } else {
                selDomain.push([fieldName, '=', values[0]]);
            }
            fullDomain = fullDomain.length > 0 ? ['&', ...fullDomain, ...selDomain] : selDomain;
        }

        // Add date filters
        for (const [fieldName, domain] of Object.entries(this.dateDomains)) {
            fullDomain = fullDomain.length > 0 ? ['&', ...fullDomain, ...domain] : domain;
        }

        this.env.searchModel.clearQuery();
        if (fullDomain.length > 0) {
            this.env.searchModel.splitAndAddDomain(fullDomain);
        }
    },

    removeTag(tagText, name) {
        if (this.state.searchTags[name]) {
            this.state.searchTags[name] = this.state.searchTags[name].filter(t => t !== tagText);
            this._updateSearchModel();
        }
    },

    changeStateSelection(name, value) {
        if (!this.state.selectedItems[name]) {
            this.state.selectedItems[name] = [];
        }
        const index = this.state.selectedItems[name].indexOf(value);
        if (index > -1) {
            this.state.selectedItems[name].splice(index, 1);
        } else {
            this.state.selectedItems[name].push(value);
        }
        this._updateSearchModel();
    },

    changeDate(name, date) {
        let domain = [];
        if (date.from && date.to) {
            domain = ['&', [name, '>=', date.from], [name, '<=', date.to]];
        } else if (date.from) {
            domain = [[name, '=', date.from]];
        } else if (date.to) {
            domain = [[name, '<=', date.to]];
        }
        if (domain.length > 0) {
            this.dateDomains[name] = domain;
        } else {
            delete this.dateDomains[name];
        }
        this._updateSearchModel();
    },
});

const renderers = [ListRenderer, FileUploadListRenderer, AccountMoveListRenderer, SaleListRenderer, PurchaseDashBoardRenderer];
for (const renderer of renderers) {
    if (renderer && renderer.components) {
        renderer.components.DateRange = DateRange;
    }
}
