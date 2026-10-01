/** @odoo-module **/

/**
 * Cybrosys Technologies Pvt. Ltd.
 *
 * Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
 * Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
 *
 * This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 * (AGPL v3), Version 3.
 */


import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CardTypeSelection extends Component {
    static template = "odoo_dynamic_dashboard.CardTypeSelection";
    static props = {
        ...standardFieldProps,
    };
    get selectedValue() {
        return this.props.record.data[this.props.name] || false;
    }
    selectOption(value) {
        if (!this.props.readonly) {
            this.props.record.update({ [this.props.name]: value });
        }
    }
    getSvgPath(value) {
        if (![
            'table', 'chart', 'block', 'to-do', 'views',
            'bar', 'line', 'area', 'pie', 'doughnut', 'polarArea','activity',
            'radial', 'scatter', 'radar', 'bubble', 'flower', 'funnel', 'hierarchy',
            'kanban', 'list', 'form', 'pivot', 'graph', 'progress', 'calendar',
            'map', 'data_grid', 'minimal_line', 'borderless', 'striped', 'classic',
            'priority','timeline','feed','summary'
        ].includes(value)) {
            value = 'unknown';
        }
        if (value === 'list') {
            return '/odoo_dynamic_dashboard/static/src/img/view_list.svg';
        }
        return '/odoo_dynamic_dashboard/static/src/img/' + value + '.svg';
    }
    isSelected(value) {
        return this.selectedValue === value;
    }
    get options() {
        const selection = this.props.record.fields[this.props.name].selection || [];
        return selection.map(([value, label]) => ({
            value,
            label,
        }));
    }
}
export const cardTypeSelection = {
    component: CardTypeSelection,
    supportedTypes: ["selection"],
};

registry.category("fields").add("card_type_selection", cardTypeSelection);