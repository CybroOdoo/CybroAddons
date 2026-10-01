/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from '@web/core/utils/hooks';
import { DashboardCardButtons } from './dashboard_card_buttons';

export class DashboardList extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService("action");

        this.state = useState({
            card: this.props.card,
            headers: [],
            rows: [],
            totalRecords: 0,
            rowsPerPage: 10,
            currentPage: 1,
            start: 1,
            end: 0,
            hasPrev: false,
            hasNext: true,
        });

        onWillStart(async () => {
            await this.loadListData();
        });

        onWillUpdateProps(async (nextProps) => {
            this.state.card = nextProps.card;
            await this.loadListData(nextProps.card);
        });
    }

    async loadListData(card = this.props.card) {
        try {
            const headers = JSON.parse(card.view_headers || '[]');
            const rows = JSON.parse(card.view_data || '[]');

            this.state.headers = headers;
            this.state.rows = rows.slice(0, this.state.rowsPerPage);
            this.state.totalRecords = rows.length;
            this.state.end = Math.min(this.state.rowsPerPage, rows.length);
            this.state.hasPrev = this.state.currentPage > 1;
            this.state.hasNext = this.state.end < this.state.totalRecords;
        } catch (e) {
            this.state.rows = [];
        }
    }

    async onRowClick(id) {
        if (this.props.card.enable_click) {
            const modelInfo = await this.orm.searchRead("ir.model",
                [["id", "=", this.props.card.model_id[0]]], ['model']);

            const cardName = this.props.card.name || this.props.card.model_name;
            this.action.doAction({
                type: "ir.actions.act_window",
                name: cardName,
                displayName: cardName,
                res_model: modelInfo[0].model,
                res_id: id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    previousPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.updatePageData();
        }
    }

    nextPage() {
        if (this.state.hasNext) {
            this.state.currentPage++;
            this.updatePageData();
        }
    }

    updatePageData() {
        const allRows = JSON.parse(this.props.card.view_data || '[]');
        const startIdx = (this.state.currentPage - 1) * this.state.rowsPerPage;
        const endIdx = startIdx + this.state.rowsPerPage;

        this.state.rows = allRows.slice(startIdx, endIdx);
        this.state.start = startIdx + 1;
        this.state.end = Math.min(endIdx, allRows.length);
        this.state.hasPrev = this.state.currentPage > 1;
        this.state.hasNext = this.state.end < allRows.length;
    }
}

DashboardList.template = 'DashboardListTemplate';
DashboardList.components = { DashboardCardButtons };
