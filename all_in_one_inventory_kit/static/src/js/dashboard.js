import { registry } from "@web/core/registry";
import { Component, signal, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class InventoryDashboard extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.result_3 = {};
        this.charts = {};

        this.pro_info = signal.ref();
        this.canvas = signal.ref();
        this.stock_moves = signal.ref();
        this.product_move_table = signal.ref();
        this.category_table = signal.ref();
        this.product_category = signal.ref();
        this.graphs = signal.ref();
        this.out_of_stock_table = signal.ref();
        this.location_table = signal.ref();
        this.product_move_graph = signal.ref();
        this.product_move_selection = signal.ref();
        this.stock_move_table = signal.ref();
        this.canvaspie = signal.ref();
        this.graph_details_table = signal.ref();
        this.operation_type_table = signal.ref();
        this.set = signal.ref();
        this.operation = signal.ref();
        this.dashboards_templates = ['all_in_one_inventory_kit.InventoryTiles', 'all_in_one_inventory_kit.ProductSaleBarGraph'];

        onMounted(this.onMounted);
    }

    async onMounted() {
        this.render_graphs();
    }

    render_graphs() {
        this.render_operation_tile();
        this.render_stock_moves();
        this.render_product_move_graph_this_month();
        this.render_product_category();
        this.render_storage_location();
        this.render_out_of_stock_graph();
        this.render_dead_of_stock_graph();
    }

    _formatText(val) {
        if (val === undefined || val === null) {
            return '';
        }
        if (typeof val === 'object') {
            return val.en_US || Object.values(val)[0] || '';
        }
        return String(val);
    }

    _formatLabels(list) {
        if (!Array.isArray(list)) return [];
        return list.map(item => this._formatText(item));
    }

    _appendTableRow(table, col1Text, col2Text, col2Class = "location_table_value") {
        if (!table) return;
        const tr = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = this._formatText(col1Text);
        const td2 = document.createElement('td');
        if (col2Class) {
            td2.className = col2Class;
        }
        td2.textContent = this._formatText(col2Text);
        tr.appendChild(td1);
        tr.appendChild(td2);
        table.appendChild(tr);
    }

    _clearTableRows(table) {
        if (!table) return;
        const rows = table.querySelectorAll('tr:not(:first-child)');
        rows.forEach(r => r.remove());
    }

    _renderChart(chartKey, canvas, config) {
        if (!canvas) return null;
        if (this.charts[chartKey]) {
            this.charts[chartKey].destroy();
        }
        const ctx = canvas.getContext ? canvas.getContext('2d') : canvas;
        const chart = new Chart(ctx, config);
        this.charts[chartKey] = chart;
        return chart;
    }

    // Append the dashboard cards
    render_operation_tile() {
        const self = this;
        rpc('/get_operation_types').then(function (result) {
            if (!result) return;
            const operation_types = result[0] || {};
            const late = result[1] || {};
            const waiting = result[2] || {};
            self.result_3 = result[3] || {};
            const backorder = result[4] || {};
            const colors = ["red", "blue", "green", "orange", "purple", "steel", "rebecca", "brown", "pink", "grey", "black"];
            const types = self.set();
            if (types) {
                types.innerHTML = '';
                let g = 0;
                Object.entries(operation_types).forEach(([key, value]) => {
                    const result_1 = key;
                    const result_2 = value;
                    const cardTitle = (self.result_3 && self.result_3[result_1]) ? self._formatText(self.result_3[result_1]) : '';

                    const div = document.createElement('div');
                    div.style.display = "contents";

                    const tileDiv = document.createElement('div');
                    tileDiv.className = "col-sm-12 col-md-6 col-lg-3";
                    tileDiv.id = result_1;
                    tileDiv.style.cursor = "pointer";
                    tileDiv.addEventListener('click', (e) => self.onclick_tiles(e));

                    const card = document.createElement('div');
                    card.className = `dashboard-card dashboard-card--border-top dashboard-card--border-top-${colors[g % colors.length]}`;

                    const details = document.createElement('div');
                    details.className = "dashboard-card__details";

                    const titleSpan = document.createElement('span');
                    titleSpan.className = "dashboard-card__title";
                    titleSpan.textContent = cardTitle;

                    const countSpan = document.createElement('span');
                    countSpan.className = "count-container";
                    countSpan.textContent = result_2;

                    details.appendChild(titleSpan);
                    details.appendChild(countSpan);
                    card.appendChild(details);

                    const statsUl = document.createElement('ul');
                    statsUl.className = "dashboard-card__stats";

                    if (key in late) {
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_late";
                        li.id = result_1;
                        li.style.cursor = "pointer";
                        li.addEventListener('click', (e) => self.onclick_late_status(e));
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_late">Late</div>
                                <div class="dashboard-card__stat-count_late">${late[key]}</div>
                            </div>`;
                        statsUl.appendChild(li);
                    }
                    if (key in waiting) {
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_waiting";
                        li.id = result_1;
                        li.style.cursor = "pointer";
                        li.addEventListener('click', (e) => self.onclick_waiting_status(e));
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_waiting">Waiting</div>
                                <div class="dashboard-card__stat-count_waiting">${waiting[key]}</div>
                            </div>`;
                        statsUl.appendChild(li);
                    }
                    if (key in backorder) {
                        const li = document.createElement('li');
                        li.className = "dashboard-card__stat_backorder";
                        li.id = result_1;
                        li.style.cursor = "pointer";
                        li.addEventListener('click', (e) => self.onclick_backorders_status(e));
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center text-dark text-decoration-none">
                                <div class="dashboard-card__stat-title_back">Backorder</div>
                                <div class="dashboard-card__stat-count_backorder">${backorder[key]}</div>
                            </div>`;
                        statsUl.appendChild(li);
                    }

                    card.appendChild(statsUl);
                    tileDiv.appendChild(card);
                    div.appendChild(tileDiv);
                    types.appendChild(div);
                    g++;
                });
            }

            const ctx = self.operation();
            if (ctx) {
                const names = Object.values(self.result_3);
                const counts = Object.values(operation_types);
                const operation_table = self.operation_type_table();
                self._clearTableRows(operation_table);
                names.forEach((nameVal, idx) => {
                    self._appendTableRow(operation_table, nameVal, counts[idx] || 0);
                });
                if (operation_table) {
                    operation_table.classList.add('d-none');
                }
                self._renderChart('operation_types', ctx, {
                    type: 'bar',
                    data: {
                        labels: self._formatLabels(names),
                        datasets: [{
                            label: 'Count',
                            data: counts,
                            backgroundColor: [
                                "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                                "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                            ],
                            borderColor: [
                                "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                                "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                            ],
                            borderWidth: 1,
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            fill: false,
                        }],
                    },
                    options: {
                        scales: { y: { beginAtZero: true } },
                        responsive: true,
                        maintainAspectRatio: false,
                    },
                });
            }
        });
    }

    // Top moving products bar graph
    render_product_move_graph_this_month() {
        const self = this;
        rpc('/get_the_top_products').then(function (result) {
            if (!result) return;
            const ctx = self.canvaspie();
            const products = result.products || [];
            const count = result.count || [];
            const table = self.graph_details_table();
            self._clearTableRows(table);
            products.forEach((prod, idx) => {
                self._appendTableRow(table, prod, count[idx] || 0, "product_moving_value");
            });
            if (table) table.classList.add('d-none');
            self._renderChart('top_products', ctx, {
                type: 'bar',
                data: {
                    labels: self._formatLabels(products),
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                            "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                        ],
                        borderColor: [
                            "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                            "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        fill: false,
                    }],
                },
                options: {
                    scales: { y: { beginAtZero: true } },
                    responsive: true,
                    maintainAspectRatio: false,
                },
            });
        });

        // Initialize category dropdown and graph for product moves
        rpc('/get_product_moves').then(function (result) {
            if (!result || !result[1]) return;
            const category_name = result[1].category_name || [];
            const category_id = result[1].category_id || [];
            const selection = self.product_move_selection();
            if (selection) {
                selection.innerHTML = '';
                category_name.forEach((name, idx) => {
                    const option = document.createElement('option');
                    option.value = category_id[idx];
                    option.textContent = self._formatText(name);
                    selection.appendChild(option);
                });
                if (selection.value) {
                    self.onclick_product_moves_selection(selection.value);
                }
            }
        });
    }

    render_product_category() {
        const self = this;
        rpc('/get_product_category').then(function (result) {
            if (!result) return;
            const ctx = self.product_category();
            const names = result.name || [];
            const counts = result.count || [];
            const table = self.category_table();
            self._clearTableRows(table);
            names.forEach((nameVal, idx) => {
                self._appendTableRow(table, nameVal, counts[idx] || 0);
            });
            if (table) table.classList.add('d-none');
            self._renderChart('product_categories', ctx, {
                type: 'doughnut',
                data: {
                    labels: self._formatLabels(names),
                    datasets: [{
                        label: 'Quantity Done',
                        data: counts,
                        backgroundColor: [
                            "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                            "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                        ],
                        borderColor: ["#003f5c"],
                        borderWidth: 1,
                        fill: false,
                    }],
                },
                options: {
                    scales: { y: { beginAtZero: true } },
                    responsive: true,
                    maintainAspectRatio: false,
                },
            });
        });
    }

    render_stock_moves() {
        const self = this;
        rpc('/get_stock_moves').then(function (result) {
            if (!result) return;
            const ctx = self.stock_moves();
            const names = result.name || [];
            const count = result.count || [];
            const table = self.stock_move_table();
            self._clearTableRows(table);
            names.forEach((nameVal, idx) => {
                self._appendTableRow(table, nameVal, count[idx] || 0);
            });
            if (table) table.classList.add('d-none');
            self._renderChart('stock_moves', ctx, {
                type: 'pie',
                data: {
                    labels: self._formatLabels(names),
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: [
                            "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                            "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                        ],
                        borderColor: [
                            "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                            "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        fill: false,
                    }],
                },
                options: {
                    scales: { y: { beginAtZero: true } },
                    responsive: true,
                    maintainAspectRatio: false,
                },
            });
        });
    }

    render_storage_location() {
        const self = this;
        rpc('/get_locations').then(function (result) {
            const table = self.location_table();
            if (!table) return;
            const tbody = table.querySelector('tbody.storage');
            if (tbody) {
                tbody.innerHTML = '';
                Object.entries(result || {}).forEach(([key, value]) => {
                    const row = document.createElement('tr');
                    const td1 = document.createElement('td');
                    td1.textContent = self._formatText(key);
                    const td2 = document.createElement('td');
                    td2.className = "location_table_value";
                    td2.textContent = self._formatText(value);
                    row.appendChild(td1);
                    row.appendChild(td2);
                    tbody.appendChild(row);
                });
            }
        });
    }

    render_out_of_stock_graph() {
        const self = this;
        rpc('/get_out_of_stock').then(function (result) {
            if (result && result.product_name && result.product_name.length > 0) {
                const graphsContainer = self.graphs();
                if (!graphsContainer) return;
                let colDiv = document.getElementById("out_of_stock_container");
                if (!colDiv) {
                    colDiv = document.createElement('div');
                    colDiv.id = "out_of_stock_container";
                    colDiv.className = 'year_to_date_graph_div col-sm-12 col-md-6 my-4';
                    colDiv.innerHTML = `
                        <div class="chart-container card-shadow" id="tiles">
                            <div style="height: 20px; max-height: 20px;">
                                <h2>Out of Stock Products</h2>
                                <button class="btn_info" id="out_of_stock_info" title="Show Details"><i class="oi oi-filled" data-icon="more_vert"></i></button>
                                <table class="graph_details_table d-none" id="out_of_stock_table">
                                    <thead><tr><th>Products</th><th>Out of Quantity</th></tr></thead>
                                    <tbody></tbody>
                                </table>
                            </div>
                            <hr/>
                            <div class="graph_canvas" style="margin-top: 30px;">
                                <canvas id="out_of_stock_graph" height="500px" width="150px"></canvas>
                            </div>
                        </div>`;
                    graphsContainer.appendChild(colDiv);

                    const infoBtn = colDiv.querySelector('#out_of_stock_info');
                    const table = colDiv.querySelector('#out_of_stock_table');
                    if (infoBtn && table) {
                        infoBtn.addEventListener('click', () => table.classList.toggle('d-none'));
                    }
                }

                const tableBody = colDiv.querySelector('#out_of_stock_table tbody');
                if (tableBody) {
                    tableBody.innerHTML = '';
                    const names = result.product_name;
                    const counts = result.total_quantity;
                    names.forEach((val, idx) => {
                        const tr = document.createElement('tr');
                        const td1 = document.createElement('td');
                        td1.textContent = self._formatText(val);
                        const td2 = document.createElement('td');
                        td2.textContent = self._formatText(counts[idx] || 0);
                        tr.appendChild(td1);
                        tr.appendChild(td2);
                        tableBody.appendChild(tr);
                    });
                }

                const canvas = colDiv.querySelector('#out_of_stock_graph');
                self._renderChart('out_of_stock', canvas, {
                    type: 'bar',
                    data: {
                        labels: self._formatLabels(result.product_name),
                        datasets: [{
                            label: 'Current Stock',
                            data: result.total_quantity,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            fill: false,
                        }],
                    },
                    options: {
                        scales: { y: { beginAtZero: true } },
                        responsive: true,
                        maintainAspectRatio: false,
                    },
                });
            }
        });
    }

    render_dead_of_stock_graph() {
        const self = this;
        rpc('/get_dead_of_stock').then(function (result) {
            if (result && result.product_name && result.product_name.length > 0) {
                const graphsContainer = self.graphs();
                if (!graphsContainer) return;
                let colDiv = document.getElementById("dead_stock_container");
                if (!colDiv) {
                    colDiv = document.createElement('div');
                    colDiv.id = "dead_stock_container";
                    colDiv.className = 'year_to_date_graph_div col-sm-12 col-md-6 my-4';
                    colDiv.innerHTML = `
                        <div class="chart-container card-shadow" id="tiles">
                            <div style="height: 20px; max-height: 20px;">
                                <h2>Dead Stock</h2>
                                <button class="btn_info" id="dead_stock_info" title="Show Details"><i class="oi oi-filled" data-icon="more_vert"></i></button>
                                <table class="graph_details_table d-none" id="dead_stock_table">
                                    <thead><tr><th>Products</th><th>Dead Quantity</th></tr></thead>
                                    <tbody></tbody>
                                </table>
                            </div>
                            <hr/>
                            <div class="graph_canvas" style="margin-top: 30px;">
                                <canvas id="dead_stock_graph" height="500px" width="150px"></canvas>
                            </div>
                        </div>`;
                    graphsContainer.appendChild(colDiv);

                    const infoBtn = colDiv.querySelector('#dead_stock_info');
                    const table = colDiv.querySelector('#dead_stock_table');
                    if (infoBtn && table) {
                        infoBtn.addEventListener('click', () => table.classList.toggle('d-none'));
                    }
                }

                const tableBody = colDiv.querySelector('#dead_stock_table tbody');
                if (tableBody) {
                    tableBody.innerHTML = '';
                    const names = result.product_name;
                    const counts = result.total_quantity;
                    names.forEach((val, idx) => {
                        const tr = document.createElement('tr');
                        const td1 = document.createElement('td');
                        td1.textContent = self._formatText(val);
                        const td2 = document.createElement('td');
                        td2.textContent = self._formatText(counts[idx] || 0);
                        tr.appendChild(td1);
                        tr.appendChild(td2);
                        tableBody.appendChild(tr);
                    });
                }

                const canvas = colDiv.querySelector('#dead_stock_graph');
                self._renderChart('dead_stock', canvas, {
                    type: 'line',
                    data: {
                        labels: self._formatLabels(result.product_name),
                        datasets: [{
                            label: 'Current Stock',
                            data: result.total_quantity,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            fill: false,
                        }],
                    },
                    options: {
                        scales: { y: { beginAtZero: true } },
                        responsive: true,
                        maintainAspectRatio: false,
                    },
                });
            }
        });
    }

    async onclick_top_product_selection(val) {
        let route = '/get_the_top_products';
        if (val === 'top_last_10_days') {
            route = '/top_products_last_ten';
        } else if (val === 'top_last_30_days') {
            route = '/top_products_last_thirty';
        } else if (val === 'top_last_3_month') {
            route = '/top_products_last_three_months';
        } else if (val === 'top_last_year') {
            route = '/top_products_last_year';
        }
        const result = await rpc(route);
        if (!result) return;
        const ctx = this.canvaspie();
        const products = result.products || [];
        const count = result.count || [];
        const table = this.graph_details_table();
        this._clearTableRows(table);
        products.forEach((prod, idx) => {
            this._appendTableRow(table, prod, count[idx] || 0, "product_moving_value");
        });
        if (table) table.classList.add('d-none');
        this._renderChart('top_products', ctx, {
            type: 'bar',
            data: {
                labels: this._formatLabels(products),
                datasets: [{
                    label: 'Count',
                    data: count,
                    backgroundColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                        "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                    ],
                    borderColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                        "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    fill: false,
                }],
            },
            options: {
                scales: { y: { beginAtZero: true } },
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    async onclick_stock_moves_selection(val) {
        let route = '/get_stock_moves';
        if (val === 'last_10_days') {
            route = '/stock_move_last_ten_days';
        } else if (val === 'this_month') {
            route = '/this_month';
        } else if (val === 'last_3_month') {
            route = '/last_three_month';
        } else if (val === 'last_year') {
            route = '/last_year';
        }
        const result = await rpc(route);
        if (!result) return;
        const ctx = this.stock_moves();
        const names = result.name || [];
        const count = result.count || [];
        const table = this.stock_move_table();
        this._clearTableRows(table);
        names.forEach((nameVal, idx) => {
            this._appendTableRow(table, nameVal, count[idx] || 0);
        });
        if (table) table.classList.add('d-none');
        this._renderChart('stock_moves', ctx, {
            type: 'pie',
            data: {
                labels: this._formatLabels(names),
                datasets: [{
                    label: 'Count',
                    data: count,
                    backgroundColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                        "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                    ],
                    borderColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
                        "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    fill: false,
                }],
            },
            options: {
                scales: { y: { beginAtZero: true } },
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    async onclick_product_moves_selection(ev) {
        const option = (ev && ev.target) ? ev.target.value : ev;
        if (!option) return;
        const result = await rpc('/product_move_by_category', { args: option });
        if (!result) return;
        const ctx = this.product_move_graph();
        const names = result.name || [];
        const count = result.count || [];
        const table = this.product_move_table();
        this._clearTableRows(table);
        names.forEach((nameVal, idx) => {
            this._appendTableRow(table, nameVal, count[idx] || 0);
        });
        if (table) table.classList.add('d-none');
        this._renderChart('product_moves', ctx, {
            type: 'line',
            data: {
                labels: this._formatLabels(names),
                datasets: [{
                    label: 'Quantity Done',
                    data: count,
                    backgroundColor: '#003f5c',
                    borderColor: '#003f5c',
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    fill: false,
                }],
            },
            options: {
                scales: { y: { beginAtZero: true } },
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    onclick_tiles(e) {
        const target = e.currentTarget;
        const id = parseInt(target.id);
        const title = (this.result_3 && this.result_3[id]) ? this._formatText(this.result_3[id]) : 'Pickings';
        this.actionService.doAction({
            name: title,
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form']],
            domain: [['picking_type_id', '=', id]],
            target: 'current',
        });
    }

    onclick_late_status(e) {
        e.stopPropagation();
        const id = parseInt(e.currentTarget.id);
        const title = ((this.result_3 && this.result_3[id]) ? this._formatText(this.result_3[id]) : '') + '/Late';
        const today = new Date().toISOString().slice(0, 10);
        this.actionService.doAction({
            name: title,
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form']],
            domain: [
                ['picking_type_id', '=', id],
                ['state', 'in', ['assigned', 'waiting', 'confirmed']],
                ['scheduled_date', '<=', today],
            ],
            target: 'current',
        });
    }

    onclick_waiting_status(e) {
        e.stopPropagation();
        const id = parseInt(e.currentTarget.id);
        const title = ((this.result_3 && this.result_3[id]) ? this._formatText(this.result_3[id]) : '') + '/Waiting';
        this.actionService.doAction({
            name: title,
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form']],
            domain: [
                ['picking_type_id', '=', id],
                ['state', '=', 'confirmed'],
            ],
            target: 'current',
        });
    }

    onclick_backorders_status(e) {
        e.stopPropagation();
        const id = parseInt(e.currentTarget.id);
        const title = ((this.result_3 && this.result_3[id]) ? this._formatText(this.result_3[id]) : '') + '/Backorders';
        this.actionService.doAction({
            name: title,
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form']],
            domain: [
                ['picking_type_id', '=', id],
                ['backorder_id', '!=', false],
            ],
            target: 'current',
        });
    }

    onclick_top_product_info() {
        const x = this.graph_details_table();
        if (x) x.classList.toggle('d-none');
    }

    onclick_pro_cate_info() {
        const x = this.category_table();
        if (x) x.classList.toggle('d-none');
    }

    onclick_location_info() {
        const x = this.location_table();
        if (x) x.classList.toggle('d-none');
    }

    onclick_operation_type_info() {
        const x = this.operation_type_table();
        if (x) x.classList.toggle('d-none');
    }

    onclick_dead_stock_info() {
        const x = document.getElementById("dead_stock_table");
        if (x) x.classList.toggle('d-none');
    }

    onclick_out_of_stock_info() {
        const x = document.getElementById("out_of_stock_table");
        if (x) x.classList.toggle('d-none');
    }

    onclick_product_move_info() {
        const x = this.product_move_table();
        if (x) x.classList.toggle('d-none');
    }

    onclick_stock_move_info() {
        const x = this.stock_move_table();
        if (x) x.classList.toggle('d-none');
    }
}

InventoryDashboard.template = 'all_in_one_inventory_kit.Dashboard';
registry.category("actions").add("inventory_dashboard_tag", InventoryDashboard);
