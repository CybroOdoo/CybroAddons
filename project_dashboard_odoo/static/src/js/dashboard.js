/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart} = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState} from "@odoo/owl";

export class ProjectDashboard extends Component {
    /**
     * Setup method to initialize required services and register event handlers.
     */
	setup() {
		this.action = useService("action");
		this.orm = useService("orm");
		this.project_doughnut = useRef("project_doughnut");
		this.project_selection = useRef("project_selection");
		this.start_date = useRef("start_date");
		this.end_date = useRef("end_date");
		this.tot_project = useRef("tot_project");
		this.tot_employee = useRef("tot_employee");
		this.tot_hrs = useRef("tot_hrs");
		this.tot_margin = useRef("tot_margin");
		this.total_task = useRef("tot_task");
		this.total_so = useRef("tot_so");
		this.employee_selection = useRef("employee_selection");
		this.top_selling_employees = useRef("top_selling_employees");
		this.state = useState({
            projects : '',
            employees: "",
        });
		this.rpc = this.env.services.rpc
		onWillStart(async () => {
		    await this.willStart();
		});
		onMounted(async () => {
		    await this.mounted()
		});
	}
	/**
     * Event handler for the 'onWillStart' event.
     */
	async willStart() {
		await this.fetch_data();
	}
	 /**
     * Event handler for the 'onMounted' event.
     * Renders various components and charts after fetching data.
     */
	async mounted() {
		// Render other components after fetching data
		this.render_project_task();
		this.render_top_employees_graph();
		this.render_filter();
	}
	/**
     * Render the project task chart.
     */
	async render_project_task() {
		var datas = await rpc("/project/task/count")
        var ctx = this.project_doughnut;
        const chart = new Chart(this.project_doughnut.el, {
            type: "doughnut",
            data: {
                labels: datas.project,
                datasets: [{
                    backgroundColor: datas.color,
                    data: datas.task
                }]
            },
            options: {
                legend: {
                    position: 'left'
                },
                cutoutPercentage: 40,
                responsive: true,
            }
        });
	}
	/**
	function for getting values to employee graph
	*/
	async render_top_employees_graph() {
		var ctx = this.top_selling_employees
		var arrays = await rpc('/employee/timesheet')
        var data = {
            labels: arrays[1],
            datasets: [{
                label: "Hours Spent",
                data: arrays[0],
                backgroundColor: [
                    "rgba(190, 27, 75,1)",
                    "rgba(31, 241, 91,1)",
                    "rgba(103, 23, 252,1)",
                    "rgba(158, 106, 198,1)",
                    "rgba(250, 217, 105,1)",
                    "rgba(255, 98, 31,1)",
                    "rgba(255, 31, 188,1)",
                    "rgba(75, 192, 192,1)",
                    "rgba(153, 102, 255,1)",
                    "rgba(10,20,30,1)"
                ],
                borderColor: [
                    "rgba(190, 27, 75, 0.2)",
                    "rgba(190, 223, 122, 0.2)",
                    "rgba(103, 23, 252, 0.2)",
                    "rgba(158, 106, 198, 0.2)",
                    "rgba(250, 217, 105, 0.2)",
                    "rgba(255, 98, 31, 0.2)",
                    "rgba(255, 31, 188, 0.2)",
                    "rgba(75, 192, 192, 0.2)",
                    "rgba(153, 102, 255, 0.2)",
                    "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
                },
            ]
        };
        //options
        var options = {
            responsive: true,
            title: {
                display: true,
                position: "top",
                text: " Time by Employees",
                fontSize: 18,
                fontColor: "#111"
            },
            legend: {
                display: false,
            },
            scales: {
                yAxes: [{
                    ticks: {
                        min: 0
                    }
                }]
            }
        };
        //create Chart class object
        var chart = new Chart(ctx.el, {
            type: 'bar',
            data: data,
            options: options
        });

	}
	/**
     * Function for getting employees for filter.
     */
	async render_filter() {
		var data = await rpc('/project/filter')
        this.state.projects = data[0]
        this.state.employees = data[1]
	}
	/**
     * Event handler to apply filters based on user selections and update the dashboard data accordingly.
     */
	async _onchangeFilter(ev) {
		this.flag = 1
		var start_date = this.start_date.el.value;
		var end_date = this.end_date.el.value;
		var employee_selection = this.employee_selection.el.value;
		var project_selection = this.project_selection.el.value;
		if (!start_date) {
			start_date = "null"
		}
		if (!end_date) {
			end_date = "null"
		}
		if (!employee_selection) {
			employee_selection = "null"
		}
		if (!project_selection) {
			project_selection = "null"
		}
		var data = await rpc('/project/filter-apply', {
			'data': {
				'start_date': start_date,
				'end_date': end_date,
				'project': project_selection,
				'employee': employee_selection
			}
		})
        self.tot_hrs = data['list_hours_recorded']
        self.tot_employee = data['total_emp']
        self.tot_project = data['total_project']
        self.tot_task = data['total_task']
        self.tot_so = data['total_so']
        this.tot_project.el.innerHTML = data['total_project'].length
        this.tot_employee.el.innerHTML = data['total_emp'].length
        this.total_task.el.innerHTML = data['total_task'].length
        this.tot_hrs.el.innerHTML = data['hours_recorded']
        this.tot_margin.el.innerHTML = data['total_margin']
        this.total_so.el.innerHTML = data['total_so'].length
    }
	/**
     * Event handler to open a list of employees and display them to the user.
     */
	tot_emp(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		} else {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				domain: [
					["id", "in", this.tot_employee]
				],
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		}
	}
	/**
	function for getting values when page is loaded
	*/
	fetch_data() {
		this.flag = 0
		var self = this;
		var def1 = rpc('/get/tiles/data').then(function(result) {
			if (result['flag'] == 1) {
				self.total_projects = result['total_projects']
				self.total_tasks = result['total_tasks']
				self.tot_task = result['total_tasks_ids']
				self.total_hours = result['total_hours']
				self.total_profitability = result['total_profitability']
				self.total_employees = result['total_employees']
				self.total_sale_orders = result['total_sale_orders']
				self.project_stage_list = result['project_stage_list']
				self.tot_so = result['sale_orders_ids']
				self.flag_user = result['flag']
				self.total_projects_ids = result['total_projects_ids']
			} else {
				self.tot_task = result['total_tasks_ids']
				self.total_projects = result['total_projects']
				self.total_tasks = result['total_tasks']
				self.total_hours = result['total_hours']
				self.total_sale_orders = result['total_sale_orders']
				self.project_stage_list = result['project_stage_list']
				self.flag_user = result['flag']
				self.tot_so = result['sale_orders_ids']
				self.total_projects_ids = result['total_projects_ids']
				self.total_projects_ids = result['total_projects_ids']
			}
		});
		/**
		function for getting values to hours table
		*/
		var def3 = rpc('/get/hours')
			.then(function(res) {
				self.hour_recorded = res['hour_recorded'];
				self.hour_recorde = res['hour_recorde'];
				self.billable_fix = res['billable_fix'];
				self.non_billable = res['non_billable'];
				self.total_hr = res['total_hr'];
			});
		var def4 = rpc('/get/task/data')
			.then(function(res) {
				self.task_data = res['project'];
			});
			return Promise.all([def1, def3, def4])
        .then(() => {
            console.log('All data has been fetched successfully.');
        })
        .catch((error) => {
            console.error('An error occurred while fetching data:', error);
        });
	}
	/**
     * Event handler to open a list of projects and display them to the user.
     */
	tot_projects(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Projects"),
				type: 'ir.actions.act_window',
				res_model: 'project.project',
				domain: [
					["id", "in", this.total_projects_ids]
				],
				view_mode: 'kanban,form',
				views: [
					[false, 'kanban'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		} else {
			if (this.tot_project) {
				this.action.doAction({
					name: _t("Projects"),
					type: 'ir.actions.act_window',
					res_model: 'project.project',
					domain: [
						["id", "in", this.tot_project]
					],
					view_mode: 'kanban,form',
					views: [
						[false, 'kanban'],
						[false, 'form']
					],
					target: 'current'
				}, options)
			}
		}
	}
	/**
     * Event handler to open a list of tasks and display them to the user.
     */
	tot_tasks(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Tasks"),
			type: 'ir.actions.act_window',
			res_model: 'project.task',
			domain: [
				["id", "in", this.tot_task]
			],
			view_mode: 'tree,kanban,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
	/**
	for opening account analytic line view
	*/
	hr_recorded(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Timesheets"),
				type: 'ir.actions.act_window',
				res_model: 'account.analytic.line',
				view_mode: 'tree,form',
				views: [
					[false, 'list']
				],
				target: 'current'
			}, options)
		} else {
			if (this.tot_hrs) {
				this.action.doAction({
					name: _t("Timesheets"),
					type: 'ir.actions.act_window',
					res_model: 'account.analytic.line',
					domain: [
						["id", "in", this.tot_hrs]
					],
					view_mode: 'tree,form',
					views: [
						[false, 'list']
					],
					target: 'current'
				}, options)
			}
		}
	}
	/**
	for opening Total Margin view
	*/
	total_margin(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Task & Margin"),
			type: 'ir.actions.act_window',
			res_model: 'timesheets.analysis.report',
			view_mode: 'tree,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
    /**
	for opening sale order view
	*/
	tot_sale(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Sale Order"),
			type: 'ir.actions.act_window',
			res_model: 'sale.order',
			domain: [
				["id", "in", this.tot_so]
			],
			view_mode: 'tree,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
	/**
     * Event handler to view a list of employees.
     * @param {Event} e - The click event.
     */
	tot_emp(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		} else {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				domain: [
					["id", "in", this.tot_employee]
				],
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)

		}
	}

	// Add this method to your ProjectDashboard class
    async resetFilters() {
        // Reset filter inputs
        this.start_date.el.value = '';
        this.end_date.el.value = '';
        this.project_selection.el.value = 'null';
        this.employee_selection.el.value = 'null';

        // Reset the flag to indicate no filters are applied
        this.flag = 0;

        // Refresh the data by calling fetch_data again
        await this.fetch_data();

        // Re-render the charts
        this.render_project_task();
        this.render_top_employees_graph();

        // Update the KPI cards with the original values
        this.tot_project.el.innerHTML = this.total_projects.length || 0;
        this.tot_employee.el.innerHTML = this.total_employees.length || 0;
        this.total_task.el.innerHTML = this.total_tasks.length || 0;
        this.tot_hrs.el.innerHTML = this.total_hours || 0;
        this.tot_margin.el.innerHTML = this.total_profitability || 0;
        this.total_so.el.innerHTML = this.total_sale_orders.length || 0;

        // Show a success notification (optional)
        this.env.services.notification.add(
            "Filters have been reset successfully",
            { type: "success" }
        );
    }
}
ProjectDashboard.template = "ProjectDashboard"
registry.category("actions").add("project_dashboard", ProjectDashboard)
