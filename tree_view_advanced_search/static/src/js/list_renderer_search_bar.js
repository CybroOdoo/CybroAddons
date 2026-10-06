/** @odoo-module */
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched, useExternalListener } from "@odoo/owl";
import { DateRange } from "./components/date_range";
import { PurchaseDashBoardRenderer } from "@purchase/views/purchase_listview";
import { SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { SaleListRenderer } from "@sale/views/sale_onboarding_list/sale_onboarding_list_renderer";
import { FileUploadListRenderer } from "@account/views/file_upload_list/file_upload_list_renderer";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.columnTags = {};       // { [fieldName]: string[] }
        this.selectedItems = {};    // { [fieldName]: string | null }
        this.columnDates = {};      // { [fieldName]: { from, to } | null }
        this.columnGroupIds = {};   // { [fieldName]: groupId }

        onMounted(() => {
            this._syncWithSearchModel();
            this._renderAllColumnTags();
        });

        onPatched(() => {
            this._syncWithSearchModel();
            this._renderAllColumnTags();
        });

        if (this.env.searchModel) {
            useExternalListener(this.env.searchModel, "update", () => {
                this._syncWithSearchModel();
                this._renderAllColumnTags();
            });
        }
    },

    _syncWithSearchModel() {
        if (!this.env.searchModel) {
            return;
        }
        const activeFacets = this.env.searchModel.facets || [];
        const activeGroupIds = new Set(activeFacets.map((f) => f.groupId));

        for (const name of Object.keys(this.columnGroupIds)) {
            if (this._isUpdatingColumnFilter === name) {
                continue;
            }
            const groupId = this.columnGroupIds[name];
            if (!activeGroupIds.has(groupId)) {
                delete this.columnGroupIds[name];

                if (this.columnTags[name] && this.columnTags[name].length > 0) {
                    this.columnTags[name] = [];
                    this.renderColumnTags(name);
                }
                if (this.selectedItems[name]) {
                    this.selectedItems[name] = null;
                }
                if (this.columnDates[name]) {
                    this.columnDates[name] = null;
                }
            }
        }
    },

    _renderAllColumnTags() {
        for (const name of Object.keys(this.columnTags)) {
            this.renderColumnTags(name);
        }
    },

    renderColumnTags(name) {
        const container = document.getElementById(name + 'Container');
        if (!container) {
            return;
        }
        const oldTags = container.querySelectorAll('.tag');
        oldTags.forEach((tag) => tag.remove());

        const tags = this.columnTags[name] || [];
        const innerDiv = container.querySelector('div');
        tags.forEach((tagText) => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = tagText;
            const removeButton = document.createElement('i');
            removeButton.className = 'fa fa-close';
            removeButton.addEventListener('click', (ev) => {
                ev.stopPropagation();
                this.removeTagText(name, tagText);
            });
            tag.appendChild(removeButton);
            if (innerDiv) {
                container.insertBefore(tag, innerDiv);
            } else {
                container.appendChild(tag);
            }
        });
    },

    addTag(tagText, name) {
        if (!this.columnTags[name]) {
            this.columnTags[name] = [];
        }
        if (!this.columnTags[name].includes(tagText)) {
            this.columnTags[name].push(tagText);
        }
        this.renderColumnTags(name);
    },

    removeTagText(name, tagText) {
        if (this.columnTags[name]) {
            const index = this.columnTags[name].indexOf(tagText);
            if (index !== -1) {
                this.columnTags[name].splice(index, 1);
            }
        }
        this.renderColumnTags(name);
        this._onColumnFilterChanged(name);
    },

    _onKeyPress(ev, name) {
        this._onKeydown(ev, name);
    },

    _onKeydown(ev, name) {
        ev.stopPropagation();
        if (ev.key === "Enter") {
            ev.preventDefault();
            const input = ev.currentTarget;
            const value = input.value.trim();
            if (value !== '') {
                this.addTag(value, name);
                input.value = '';
                this._onColumnFilterChanged(name);
            }
        } else if (ev.key === "Backspace") {
            const input = ev.currentTarget;
            if (input.value === '' && this.columnTags[name] && this.columnTags[name].length > 0) {
                ev.preventDefault();
                const lastTag = this.columnTags[name][this.columnTags[name].length - 1];
                this.removeTagText(name, lastTag);
            }
        }
    },

    _onClickSearch(ev, name) {
        ev.stopPropagation();
        const input = document.getElementById(name + 'Input');
        const value = input ? input.value.trim() : '';
        if (value !== '') {
            this.addTag(value, name);
            if (input) {
                input.value = '';
            }
            this._onColumnFilterChanged(name);
        }
    },

    getSelectedItem(name) {
        return this.selectedItems[name] || null;
    },

    changeStateSelection(name, value) {
        if (this.selectedItems[name] === value) {
            this.selectedItems[name] = null;
        } else {
            this.selectedItems[name] = value;
        }
        this._onColumnFilterChanged(name);
    },

    changeDate(name, date) {
        if (date && (date.from || date.to)) {
            this.columnDates[name] = date;
        } else {
            this.columnDates[name] = null;
        }
        this._onColumnFilterChanged(name);
    },

    _buildDomainForField(name) {
        const Domain = [];
        const tags = this.columnTags[name] || [];
        if (tags.length === 1) {
            Domain.push([name, 'ilike', tags[0]]);
        } else if (tags.length > 1) {
            for (let i = 0; i < tags.length; i++) {
                if (i < tags.length - 1) {
                    Domain.push('|');
                }
                Domain.push([name, 'ilike', tags[i]]);
            }
        }

        if (this.selectedItems[name]) {
            if (Domain.length > 0) {
                Domain.unshift('&');
            }
            Domain.push([name, 'ilike', this.selectedItems[name]]);
        }

        if (this.columnDates[name]) {
            const date = this.columnDates[name];
            let dateDomain = [];
            if (date.from && date.to) {
                dateDomain = ['&', [name, '>=', date.from], [name, '<=', date.to]];
            } else if (date.from) {
                dateDomain = [[name, '>=', date.from]];
            } else if (date.to) {
                dateDomain = [[name, '<=', date.to]];
            }
            if (dateDomain.length > 0) {
                if (Domain.length > 0) {
                    Domain.unshift('&');
                    Domain.push(...dateDomain);
                } else {
                    Domain.push(...dateDomain);
                }
            }
        }
        return Domain;
    },

    async _onColumnFilterChanged(name) {
        if (!this.env.searchModel) {
            return;
        }
        this._isUpdatingColumnFilter = name;
        try {
            const Domain = this._buildDomainForField(name);
            const oldGroupId = this.columnGroupIds[name];

            if (Domain.length > 0) {
                const beforeGroupIds = new Set((this.env.searchModel.facets || []).map((f) => f.groupId));

                await this.env.searchModel.splitAndAddDomain(Domain, oldGroupId);

                const afterFacets = this.env.searchModel.facets || [];
                const newFacet = afterFacets.find((f) => !beforeGroupIds.has(f.groupId));
                if (newFacet) {
                    this.columnGroupIds[name] = newFacet.groupId;
                } else {
                    const matchFacet = afterFacets.find((f) => f.groupId === oldGroupId) || afterFacets[afterFacets.length - 1];
                    if (matchFacet) {
                        this.columnGroupIds[name] = matchFacet.groupId;
                    }
                }
            } else if (oldGroupId) {
                this.env.searchModel.deactivateGroup(oldGroupId);
                delete this.columnGroupIds[name];
            }
        } finally {
            this._isUpdatingColumnFilter = null;
        }
    },
});

ListRenderer.components = { ...ListRenderer.components, DateRange };
PurchaseDashBoardRenderer.components = { ...PurchaseDashBoardRenderer.components, DateRange };
SectionAndNoteListRenderer.components = { ...SectionAndNoteListRenderer.components, DateRange };
SaleListRenderer.components = { ...SaleListRenderer.components, DateRange };
FileUploadListRenderer.components = { ...FileUploadListRenderer.components, DateRange };
