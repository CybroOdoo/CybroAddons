/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onMounted, onWillStart, proxy, signal } from "@odoo/owl";

/**
 * Helper to create a signal ref that also provides a getter for `.el`
 * to maintain compatibility with code and external callers accessing `.el`.
 */
function createRef() {
    const ref = signal.ref();
    Object.defineProperty(ref, "el", {
        get() {
            return ref();
        },
    });
    return ref;
}

export class ProjectDashboard extends Component {
    /**
     * Setup method to initialize required services and register event handlers.
     */
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.project_doughnut = createRef();
        this.project_selection = createRef();
        this.start_date = createRef();
        this.end_date = createRef();
        this.employee_selection = createRef();
        this.top_selling_employees = createRef();

        this.tot_project_ref = createRef();
        this.tot_employee_ref = createRef();
        this.tot_task_ref = createRef();
        this.tot_hrs_ref = createRef();
        this.tot_margin_ref = createRef();
        this.tot_so_ref = createRef();

        // Ref aliases for backwards compatibility
        this.total_task = this.tot_task_ref;
        this.total_so = this.tot_so_ref;

        this.state = proxy({
            projects: [],
            employees: [],
            total_projects: 0,
            total_employees: 0,
            total_tasks: 0,
            total_hours: 0,
            total_profitability: 0,
            total_sale_orders: 0,
            task_data: [],
            project_stage_list: [],
            flag_user: 1,
        });

        this.flag = 0;
        this.total_projects_ids = [];
        this.tot_project = [];
        this.tot_employee = [];
        this.tot_task = [];
        this.tot_hrs = [];
        this.tot_so = [];

        onWillStart(async () => {
            await this.willStart();
        });
        onMounted(async () => {
            await this.mounted();
        });
    }

    get total_projects() { return this.state.total_projects; }
    set total_projects(val) { this.state.total_projects = val; }
    get total_employees() { return this.state.total_employees; }
    set total_employees(val) { this.state.total_employees = val; }
    get total_tasks() { return this.state.total_tasks; }
    set total_tasks(val) { this.state.total_tasks = val; }
    get total_hours() { return this.state.total_hours; }
    set total_hours(val) { this.state.total_hours = val; }
    get total_profitability() { return this.state.total_profitability; }
    set total_profitability(val) { this.state.total_profitability = val; }
    get total_sale_orders() { return this.state.total_sale_orders; }
    set total_sale_orders(val) { this.state.total_sale_orders = val; }
    get task_data() { return this.state.task_data; }
    set task_data(val) { this.state.task_data = val; }
    get project_stage_list() { return this.state.project_stage_list; }
    set project_stage_list(val) { this.state.project_stage_list = val; }
    get flag_user() { return this.state.flag_user; }
    set flag_user(val) { this.state.flag_user = val; }
    get formatted_profitability() {
        const val = Number(this.state.total_profitability) || 0;
        const sign = val < 0 ? "-" : "";
        const absVal = Math.abs(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        const symbol = this.currency_symbol || '$';
        return `${sign}${symbol}${absVal}`;
    }

    /**
     * Event handler for the 'onWillStart' event.
     */
    async willStart() {
        await loadBundle("web.chartjs_lib");
        await this.fetch_data();
    }

    /**
     * Event handler for the 'onMounted' event.
     * Renders various components and charts after fetching data.
     */
    async mounted() {
        await this.render_project_task();
        await this.render_top_employees_graph();
        await this.render_filter();
    }

    /**
     * Render the project task doughnut chart with modern styling matching the reference design.
     */
    async render_project_task() {
        const context = user.context || {};
        const datas = await rpc("/project/task/count", { context });
        const canvas = this.project_doughnut.el || this.project_doughnut();
        if (!canvas) {
            return;
        }
        if (this.projectTaskChart) {
            this.projectTaskChart.destroy();
            this.projectTaskChart = null;
        }

        // Modern palette matching reference screenshot (cyan, deep navy, blue, violet, emerald)
        const modernPalette = [
            "#00c2cb", "#1b2a47", "#2b74ff", "#38bdf8", "#6366f1", 
            "#10b981", "#f59e0b", "#f43f5e", "#94a3b8", "#0284c7"
        ];
        const colors = datas.color && datas.color.length ? datas.color : modernPalette;

        this.projectTaskChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: datas.project || [],
                datasets: [{
                    backgroundColor: colors,
                    hoverBackgroundColor: colors,
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    data: datas.task || []
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'left',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 11
                            },
                            color: '#64748b'
                        }
                    }
                },
                cutout: '65%',
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    animateScale: true,
                    animateRotate: true
                }
            }
        });
    }

    /**
     * Function for getting values to employee graph with modern rounded bar styling.
     */
    async render_top_employees_graph() {
        const context = user.context || {};
        const arrays = await rpc('/employee/timesheet', { context });
        const canvas = this.top_selling_employees.el || this.top_selling_employees();
        if (!canvas) {
            return;
        }
        if (this.employeeTimesheetChart) {
            this.employeeTimesheetChart.destroy();
            this.employeeTimesheetChart = null;
        }

        const labels = (arrays && arrays[1]) || [];
        const dataValues = (arrays && arrays[0]) || [];

        // Dual-tone color pattern matching the screenshot's bar styling (cyan & navy)
        const bgColors = dataValues.map((_, idx) => idx % 2 === 0 ? "#00c2cb" : "#1b2a47");

        const data = {
            labels: labels,
            datasets: [{
                label: "Hours Spent",
                data: dataValues,
                backgroundColor: bgColors,
                borderWidth: 0,
                barPercentage: 0.6,
                categoryPercentage: 0.75
            }]
        };

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: "#94a3b8",
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "rgba(226, 232, 240, 0.6)",
                        drawBorder: false
                    },
                    ticks: {
                        color: "#94a3b8",
                        font: {
                            size: 10
                        }
                    }
                }
            }
        };

        this.employeeTimesheetChart = new Chart(canvas, {
            type: 'bar',
            data: data,
            options: options
        });
    }

    /**
     * Function for getting employees for filter.
     */
    async render_filter() {
        const context = user.context || {};
        const data = await rpc('/project/filter', { context });
        this.state.projects = data[0] || [];
        this.state.employees = data[1] || [];
    }

    /**
     * Event handler to apply filters based on user selections and update the dashboard data accordingly.
     */
    async _onchangeFilter(ev) {
        this.flag = 1;
        let start_date = this.start_date.el ? this.start_date.el.value : "null";
        let end_date = this.end_date.el ? this.end_date.el.value : "null";
        let employee_selection = this.employee_selection.el ? this.employee_selection.el.value : "null";
        let project_selection = this.project_selection.el ? this.project_selection.el.value : "null";
        if (!start_date) {
            start_date = "null";
        }
        if (!end_date) {
            end_date = "null";
        }
        if (!employee_selection) {
            employee_selection = "null";
        }
        if (!project_selection) {
            project_selection = "null";
        }
        const context = user.context || {};
        const data = await rpc('/project/filter-apply', {
            'data': {
                'start_date': start_date,
                'end_date': end_date,
                'project': project_selection,
                'employee': employee_selection
            },
            'context': context
        });

        this.tot_hrs = data['list_hours_recorded'] || [];
        this.tot_employee = data['total_emp'] || [];
        this.tot_project = data['total_project'] || [];
        this.tot_task = data['total_task'] || [];
        this.tot_margin_ids = data['total_margin_ids'] || [];
        this.tot_so = data['total_so'] || [];

        this.state.total_projects = (data['total_project'] || []).length;
        this.state.total_employees = (data['total_emp'] || []).length;
        this.state.total_tasks = (data['total_task'] || []).length;
        this.state.total_hours = data['hours_recorded'] || 0;
        this.state.total_profitability = data['total_margin'] || 0;
        this.state.total_sale_orders = (data['total_so'] || []).length;

        if (this.tot_project_ref.el) this.tot_project_ref.el.innerHTML = this.state.total_projects;
        if (this.tot_employee_ref.el) this.tot_employee_ref.el.innerHTML = this.state.total_employees;
        if (this.tot_task_ref.el) this.tot_task_ref.el.innerHTML = this.state.total_tasks;
        if (this.tot_hrs_ref.el) this.tot_hrs_ref.el.innerHTML = this.state.total_hours;
        if (this.tot_margin_ref.el) this.tot_margin_ref.el.innerHTML = this.formatted_profitability;
        if (this.tot_so_ref.el) this.tot_so_ref.el.innerHTML = this.state.total_sale_orders;
    }

    /**
     * Event handler to open a list of employees and display them to the user.
     */
    tot_emp(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.total_employees_ids || []) : (this.tot_employee || []);
        this.action.doAction({
            name: _t("Employees"),
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            domain: [
                ["id", "in", domainIds]
            ],
            view_mode: 'kanban,list,form',
            views: [
                [false, 'kanban'],
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    /**
     * Function for getting values when page is loaded.
     */
    async fetch_data() {
        this.flag = 0;
        const context = user.context || {};
        const [tilesData, hoursData, taskData] = await Promise.all([
            rpc('/get/tiles/data', { context }),
            rpc('/get/hours', { context }),
            rpc('/get/task/data', { context })
        ]);

        this.total_projects = tilesData['total_projects'] || 0;
        this.total_projects_ids = tilesData['total_projects_ids'] || [];
        this.tot_project = this.total_projects_ids;

        this.total_employees = tilesData['total_employees'] || 0;
        this.total_employees_ids = tilesData['total_employees_ids'] || [];
        this.tot_employee = this.total_employees_ids;

        this.total_tasks = tilesData['total_tasks'] || 0;
        this.total_tasks_ids = tilesData['total_tasks_ids'] || [];
        this.tot_task = this.total_tasks_ids;

        this.total_hours = tilesData['total_hours'] || 0;
        this.total_hours_ids = tilesData['total_hours_ids'] || [];
        this.tot_hrs = this.total_hours_ids;

        this.total_profitability = tilesData['total_profitability'] || 0;
        this.total_margin_ids = tilesData['total_margin_ids'] || [];
        this.tot_margin_ids = this.total_margin_ids;

        this.total_sale_orders = tilesData['total_sale_orders'] || 0;
        this.sale_orders_ids = tilesData['sale_orders_ids'] || [];
        this.tot_so = this.sale_orders_ids;

        this.project_stage_list = tilesData['project_stage_list'] || [];
        this.project_kanban_view_id = tilesData['project_kanban_view_id'] || false;
        this.currency_symbol = tilesData['currency_symbol'] || '$';
        this.flag_user = tilesData['flag'] || 1;

        // Keep original counts for resetting filters
        this.orig_total_projects = this.total_projects;
        this.orig_total_tasks = this.total_tasks;
        this.orig_total_hours = this.total_hours;
        this.orig_total_profitability = this.total_profitability;
        this.orig_total_employees = this.total_employees;
        this.orig_total_sale_orders = this.total_sale_orders;

        this.hour_recorded = hoursData['hour_recorded'];
        this.hour_recorde = hoursData['hour_recorde'];
        this.billable_fix = hoursData['billable_fix'];
        this.non_billable = hoursData['non_billable'];
        this.total_hr = hoursData['total_hr'];

        this.task_data = taskData['project'] || [];
    }

    /**
     * Event handler to open a list of projects and display them to the user.
     */
    async tot_projects(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.total_projects_ids || []) : (this.tot_project || []);
        try {
            const action = await this.action.loadAction("project.open_view_project_all");
            action.domain = [["id", "in", domainIds]];
            await this.action.doAction(action, options);
        } catch {
            const kanbanViewId = this.project_kanban_view_id || false;
            await this.action.doAction({
                name: _t("Projects"),
                type: 'ir.actions.act_window',
                res_model: 'project.project',
                domain: [
                    ["id", "in", domainIds]
                ],
                view_mode: 'kanban,list,form',
                views: [
                    [kanbanViewId, 'kanban'],
                    [false, 'list'],
                    [false, 'form']
                ],
                context: {
                    'sale_show_partner_name': true,
                    'display_milestone_deadline': true,
                },
                target: 'current'
            }, options);
        }
    }

    /**
     * Event handler to open a list of tasks and display them to the user.
     */
    tot_tasks(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.total_tasks_ids || []) : (this.tot_task || []);
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", domainIds]
            ],
            view_mode: 'list,kanban,form',
            views: [
                [false, 'list'],
                [false, 'kanban'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    /**
     * For opening account analytic line view.
     */
    hr_recorded(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.total_hours_ids || []) : (this.tot_hrs || []);
        this.action.doAction({
            name: _t("Timesheets"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            domain: [
                ["id", "in", domainIds]
            ],
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    /**
     * For opening Total Margin view.
     */
    total_margin(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.total_margin_ids || []) : (this.tot_margin_ids || []);
        this.action.doAction({
            name: _t("Task & Margin"),
            type: 'ir.actions.act_window',
            res_model: 'timesheets.analysis.report',
            domain: [
                ["id", "in", domainIds]
            ],
            view_mode: 'list,pivot,graph,form',
            views: [
                [false, 'list'],
                [false, 'pivot'],
                [false, 'graph'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    /**
     * For opening sale order view.
     */
    tot_sale(e) {
        e.stopPropagation();
        e.preventDefault();
        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const domainIds = (this.flag === 0) ? (this.sale_orders_ids || []) : (this.tot_so || []);
        this.action.doAction({
            name: _t("Sales Orders"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            domain: [
                ["id", "in", domainIds]
            ],
            view_mode: 'list,kanban,form',
            views: [
                [false, 'list'],
                [false, 'kanban'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    /**
     * Reset filters and restore initial dashboard data.
     */
    async resetFilters() {
        if (this.start_date.el) this.start_date.el.value = '';
        if (this.end_date.el) this.end_date.el.value = '';
        if (this.project_selection.el) this.project_selection.el.value = 'null';
        if (this.employee_selection.el) this.employee_selection.el.value = 'null';

        this.flag = 0;

        await this.fetch_data();

        await this.render_project_task();
        await this.render_top_employees_graph();

        if (this.tot_project_ref.el) this.tot_project_ref.el.innerHTML = this.total_projects;
        if (this.tot_employee_ref.el) this.tot_employee_ref.el.innerHTML = this.total_employees;
        if (this.tot_task_ref.el) this.tot_task_ref.el.innerHTML = this.total_tasks;
        if (this.tot_hrs_ref.el) this.tot_hrs_ref.el.innerHTML = this.total_hours;
        if (this.tot_margin_ref.el) this.tot_margin_ref.el.innerHTML = this.formatted_profitability;
        if (this.tot_so_ref.el) this.tot_so_ref.el.innerHTML = this.total_sale_orders;

        if (this.notification) {
            this.notification.add(
                _t("Filters have been reset successfully"),
                { type: "success" }
            );
        }
    }

    /**
     * Refresh the dashboard data and re-render charts.
     */
    async refreshDashboard() {
        await this.fetch_data();
        await this.render_project_task();
        await this.render_top_employees_graph();
    }
}
ProjectDashboard.template = "ProjectDashboard";
registry.category("actions").add("project_dashboard", ProjectDashboard);
