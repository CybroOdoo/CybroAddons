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
import { Component, useEffect, useState } from "@odoo/owl";
import { DynamicDashboardCard } from "./dynamic_dashboard_card";
import { DashboardChart } from './dashboard_chart';
import { DashboardTable } from './dashboard_table';
import { DashboardTile } from './dashboard_tile';
import { DashboardView } from './dashboard_view';
import { DashboardTodo } from './dashboard_todo';
import { DashboardActivity } from './dashboard_activity';






class CardPreview extends Component {
    setup() {
        this.state = useState({
            card: this.props.record.data,
            todos: [],
        });

        const updateState = () => {
            this.state.card = this.props.record.data;

            // Extract todos from One2Many field
            const todoField = this.props.record.data.todo_ids;
            if (todoField && todoField.records) {
                this.state.todos = todoField.records.map(r => {
                    return {
                        id: r.data.id || r.resId,
                        name: r.data.name,
                        is_done: r.data.is_done,
                        status: r.data.status,
                    };
                });
            } else {
                this.state.todos = [];
            }
        }

        // Initial setup
        updateState();

        useEffect(() => {
            updateState();
        },
            () => [
                ...Object.values(this.props.record.data),
            ])
    }
    static components = {
        PreviewChart: DashboardChart,
        PreviewTile: DashboardTile,
        PreviewTable: DashboardTable,
        PreviewViews: DashboardView,
        PreviewTodo: DashboardTodo,
        PreviewActivity :DashboardActivity
    };
}
CardPreview.template = "CardPreviewTemplate";
export const cardPreview = {
    component: CardPreview,
};
registry.category("view_widgets").add("card_preview", cardPreview);