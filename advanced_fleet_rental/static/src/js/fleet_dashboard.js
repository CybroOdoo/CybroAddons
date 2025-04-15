/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"
import { jsonrpc } from "@web/core/network/rpc_service";

const { Component, onMounted, onWillStart,  useRef, useState } = owl

export class FleetDashboard extends Component {
/* Extending the component and creating class FleetDashboard */
    setup(){
        this.state = useState({
            data:{},
            chart: [],
        })
        this.orm = useService("orm");
        this.action = useService("action");
        this.Invoice = useRef("MonthlyInvoice");
        this.Duration = useRef("ContractDuration");
        onWillStart(async () => {
            await this.FetchData();
        })
        onMounted(async () =>{
            this.renderChart();
        })
    }

    async FetchData(){
    /* Function for fetching datas for dashboard */
        this.state.data = await this.orm.call("fleet.dashboard", "get_datas");
        this.state.monthlyInvoices = await this.orm.call("fleet.dashboard", "get_monthly_contract_invoices");
    }

    async renderChart(){
    /* Function for rendering different charts */
        this.charts(this.Invoice.el,'bar',this.state.monthlyInvoices.labels,'Monthly Contract Invoices',this.state.monthlyInvoices.data)
         const labels = ['Operational', 'Under Maintenance'];
         const data = [this.state.data.operational, this.state.data.under_maintenance];
        this.charts(this.Duration.el,'pie',labels,'Travel',data)
    }


  charts(canvas, type, labels, label, data) {
    let backgroundColors, borderColors;
    if (type === 'pie') {
        // Specific colors for pie chart
backgroundColors = ['rgba(46, 204, 113, 0.8)', 'rgba(231, 76, 60, 0.8)']; // Vibrant Green and Red
borderColors = ['rgba(39, 174, 96, 1)', 'rgba(192, 57, 43, 1)']; // Darker Green and Red
    } else {
        // Colors for other chart types (like bar)
        const colors = [
            'rgba(75, 192, 192, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 206, 86, 0.8)'
        ];
        const borders = [
            'rgba(75, 192, 192, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)'
        ];
        backgroundColors = data.map((_, index) => colors[index % colors.length]);
        borderColors = data.map((_, index) => borders[index % borders.length]);
    }

    const chartConfig = {
        type: type,
        data: {
            labels: labels,
            datasets: [
                {
                    label: label,
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: label
                }
            }
        }
    };

    // Add scales only for bar chart
    if (type === 'bar') {
        chartConfig.options.scales = {
            y: {
                beginAtZero: true
            }
        };
    }

    this.state.chart.push(new Chart(canvas, chartConfig));
}





    onClickVehicles(){
    /* Function for viewing Total Vehicles */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Operational Vehicles',
            res_model: 'fleet.vehicle',
            view_mode: 'tree,form',
            context: {'tree_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_tree',
            'form_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_form',
            'create': false
            },
            views: [[false, 'list'], [false, 'form']],
        })
    }
onClickAvailableVehicles() {
    /* Function for viewing Available Vehicles */
    this.action.doAction({
        type: 'ir.actions.act_window',
        name: 'Total Vehicles',
        res_model: 'fleet.vehicle',
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        context: {
        'tree_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_tree',
        'form_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_form',
        'create': false},
        target: 'current',
        domain: [['status', '=', 'operational']],
    });
}

onClickUnderMaintenanceVehicles(){
    /* Function for viewing Under Maintenance Vehicles */
    this.action.doAction({
        type: 'ir.actions.act_window',
        name: 'Under Maintenance Vehicles',
        res_model: 'fleet.vehicle',
        view_mode: 'tree,form',
        views: [[false, 'list'], [false, 'form']],
        context: {
        'tree_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_tree',
        'form_view_ref': 'advanced_fleet_rental.fleet_vehicle_view_form',
        'create': false},
        target: 'current',
        domain: [['status', '=', 'undermaintenance']],
    });
}
    onClickAllCustomers(){
    /* Function for viewing Customers */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Customers',
            res_model: 'res.partner',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            context: {"create": false},
        })
    }
    onClickInvoices(){
    /* Function for viewing Invoices */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Invoices',
            res_model: 'account.move',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            context: {"create": false},
            domain: "[('vehicle_rental_id', '!=', False)]"
        })
    }
    onPendingInvoices(){
    /* Function for viewing Pending Invoices */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Pending Invoices',
            res_model: 'account.move',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            context: {
                create: false
            },
            domain: "[('vehicle_rental_id', '!=', False)], ('state', '=', 'posted'), ('payment_state', '!=', 'paid')"
  })
    }
onAllContract(){
    /* Function for viewing All Contracts */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'All Contracts',
            res_model: 'fleet.rental.contract',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
        })
    }
onInProgressContract(){
    /* Function for viewing In progress Contracts */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'In Progress Contracts',
            res_model: 'fleet.rental.contract',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'in_progress']],
        })
    }

onReturnContract(){
    /* Function for viewing Return Contracts */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Return Contracts',
            res_model: 'fleet.rental.contract',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'return']],
        })
    }

onCancelContract(){
    /* Function for viewing Cancel Contracts */
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Cancelled Contracts',
            res_model: 'fleet.rental.contract',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'cancel']],
        })
    }
}

FleetDashboard.template = "FleetDashboard"
registry.category("actions").add('fleet_dashboard_tag', FleetDashboard)
