/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted, useEffect } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { DashboardCardButtons } from './dashboard_card_buttons';
import { user } from "@web/core/user";
export class DashboardTable extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
        const allBatches = JSON.parse(this.props.card.table_rows);
        var model = this.props.card.model_id.display_name ? this.props.card.model_id.display_name : this.props.card.model_id[1]
        this.state = useState({
            card: this.props.card,
            headers: JSON.parse(this.props.card.table_headers),
            allBatches: allBatches,
            res_model: String(model),
            rows: allBatches[0] || [],
            currentPage: 1,
            rowsPerPage: this.props.card.table_limit || 10,
            totalPages: allBatches.length,
            totalRecords: allBatches.reduce((sum, batch) => sum + batch.length, 0),
            tableClass: ''
        });
        onWillStart(async () => {
            await this.loadTableData();
        })
        useEffect(() => { this.loadTableData() }, () => [...Object.values(this.props.card)])
    }
    async onRowClick(id) {
        if (this.props.dashboard && this.props.card.enable_click) {
            var ResModel = await this.orm.searchRead(
                "ir.model",
                [["id", "=", this.props.card.model_id[0]]],
                ['model']);
            const cardName = this.props.card.name || this.props.card.model_name;
            this.action.doAction({
                type: "ir.actions.act_window",
                name: cardName,
                displayName: cardName,
                res_model: ResModel[0].model,
                target: "current",
                res_id: id,
                views: [[false, "form"]],
            });
        }
    }
    async loadTableData() {
        this.state.card = this.props.card;
        var model = this.props.card.model_id.display_name ? this.props.card.model_id.display_name : this.props.card.model_id[1];
        this.state.res_model = String(model);
        this.getTableClass()
        this.state.headers = JSON.parse(this.props.card.table_headers || "[]");
        const allBatches = JSON.parse(this.props.card.table_rows || "[]");
        this.state.allBatches = allBatches;
        this.state.totalPages = allBatches.length;
        this.state.totalRecords = allBatches.reduce((sum, batch) => sum + batch.length, 0);
        this.state.rowsPerPage = this.props.card.table_limit || 10;
        this.state.currentPage = 1;
        this.state.rows = allBatches[0] || [];
    }


    getCurrentRangeStart() {
        return ((this.state.currentPage - 1) * this.state.rowsPerPage) + 1;
    }
    // Pagination methods
    goToPage(pageNumber) {
        if (pageNumber >= 1 && pageNumber <= this.state.totalPages) {
            this.state.currentPage = pageNumber;
            this.state.rows = this.state.allBatches[pageNumber - 1] || [];
        }
    }
    getCurrentRangeEnd() {
        const currentBatchSize = this.state.rows.length;
        return ((this.state.currentPage - 1) * this.state.rowsPerPage) + currentBatchSize;
    }

    previousPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.state.rows = this.state.allBatches[this.state.currentPage - 1] || [];
        }
    }

    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            this.state.rows = this.state.allBatches[this.state.currentPage - 1] || [];
        }
    }

    firstPage() {
        this.state.currentPage = 1;
        this.state.rows = this.state.allBatches[0] || [];
    }

    lastPage() {
        this.state.currentPage = this.state.totalPages;
        this.state.rows = this.state.allBatches[this.state.totalPages - 1] || [];
    }

    getPageNumbers() {
        const pages = [];
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.state.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(this.state.totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        return pages;
    }


    getCellBadgeClass(cell, value) {
        if (cell.type === 'boolean') {
            return value ? 'badge-success' : 'badge-secondary';
        }
        return '';
    }

    getTableClass() {
        const typeMap = {
            'striped': 'table-striped',
            'borderless': 'table-borderless',
            'minimal_line': 'table-minimal-line',
            'data_grid': 'table-data-grid',
        };
        this.state.tableClass = typeMap[this.props.card.table_type] || 'table-striped';
    }

    getFieldClass(fieldType) {
        const classMap = {
            'float': 'text-right font-weight-bold',
            'monetary': 'text-right font-weight-bold',
            'integer': 'text-right',
            'boolean': 'text-center',
            'date': 'text-muted',
            'datetime': 'text-muted',
        };
        return classMap[fieldType] || '';
    }
}
DashboardTable.template = 'DashboardTableTemplate';
DashboardTable.components = { DashboardCardButtons };