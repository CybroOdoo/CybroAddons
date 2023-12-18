/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted} = owl
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

export class ProjectDashboard extends Component {
    /**
     * Setup method to initialize required services and register event handlers.
     */
	setup() {
		this.action = useService("action");
		this.orm = useService("orm");
		this.rpc = this.env.services.rpc
		onWillStart(this.onWillStart);
		onMounted(this.onMounted);
	}
	/**
     * Event handler for the 'onWillStart' event.
     */
	async onWillStart() {
		await this.fetch_data();
	}
	 /**
     * Event handler for the 'onMounted' event.
     * Renders various components and charts after fetching data.
     */
	async onMounted() {
		// Render other components after fetching data
		this.render_project_task();
		this.render_top_employees_graph();
		this.render_filter();
	}
	/**
     * Render the project task chart.
     */
	async render_project_task() {
		await jsonrpc("/project/task/count").then(function(data) {
			var ctx = $("#project_doughnut");
			new Chart(ctx, {
				type: "doughnut",
				data: {
					labels: data.project,
					datasets: [{
						backgroundColor: data.color,
						data: data.task
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
		})
	}
	/**
	function for getting values to employee graph
	*/
	async render_top_employees_graph() {
		var ctx = $(".top_selling_employees");
		await jsonrpc('/employee/timesheet').then(function(arrays) {
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
			var chart = new Chart(ctx, {
				type: 'bar',
				data: data,
				options: options
			});

		});
	}
	/**
     * Function for getting employees for filter.
     */
	render_filter() {
		jsonrpc('/project/filter').then(function(data) {
			var projects = data[0]
			var employees = data[1]
			$(projects).each(function(project) {
				$('#project_selection').append("<option value=" + projects[project].id + ">" + projects[project].name + "</option>");
			});
			$(employees).each(function(employee) {
				$('#employee_selection').append("<option value=" + employees[employee].id + ">" + employees[employee].name + "</option>");
			});
		})
	}
	/**
     * Event handler to apply filters based on user selections and update the dashboard data accordingly.
     */
	_onchangeFilter(ev) {
		this.flag = 1
		var start_date = $('#start_date').val();
		var end_date = $('#end_date').val();
		var employee_selection = $('#employee_selection').val();
		var project_selection = $('#project_selection').val();
		var self = this;
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
		jsonrpc('/project/filter-apply', {
			'data': {
				'start_date': start_date,
				'end_date': end_date,
				'project': project_selection,
				'employee': employee_selection
			}
		}).then(function(data) {
			self.tot_hrs = data['list_hours_recorded']
			self.tot_employee = data['total_emp']
			self.tot_project = data['total_project']
			self.tot_task = data['total_task']
			self.tot_so = data['total_so']
			$('#tot_project')[0].innerHTML = data['total_project'].length
			$('#tot_employee')[0].innerHTML = data['total_emp'].length
			$("#tot_task")[0].innerHTML = data['total_task'].length
			$("#tot_hrs")[0].innerHTML = data['hours_recorded']
			$("#tot_margin")[0].innerHTML = data['total_margin']
			$("#tot_so")[0].innerHTML = data['total_so'].length
		})
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
		var def1 = jsonrpc('/get/tiles/data').then(function(result) {
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
			}
		});
		/**
		function for getting values to hours table
		*/
		var def3 = jsonrpc('/get/hours')
			.then(function(res) {
				self.hour_recorded = res['hour_recorded'];
				self.hour_recorde = res['hour_recorde'];
				self.billable_fix = res['billable_fix'];
				self.non_billable = res['non_billable'];
				self.total_hr = res['total_hr'];
			});

		var def4 = jsonrpc('/get/task/data')
			.then(function(res) {
				self.task_data = res['project'];
			});
		return $.when(def1, def3, def4);
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
}
ProjectDashboard.template = "ProjectDashboard"
registry.category("actions").add("project_dashboard", ProjectDashboard)
