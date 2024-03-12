/** @odoo-module */
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { session } from '@web/session';
const { Component, useRef, onMounted ,useState } = owl

export class SalesDashboard extends Component {
//    Extending Component
    setup(){
        this.state = useState({
            data:{},
            chart:[],
            lead_customer_data: {},
            date:{},
        })
        this.action = useService("action");
        this.LeadCustomer = useRef("LeadCustomer");
        this.LeadProducts = useRef("LeadProducts");
        this.LeadSaleOrders = useRef("LeadSaleOrders");
        this.SalesTeamRevenue = useRef("SalesTeamRevenue");
        this.LeastSoldProduct = useRef("LeastSoldProduct");
        this.MonthlyQuotation = useRef("MonthlyQuotation");
        this.orm = useService("orm");
        onMounted(async()=> {
            await this.FetchData();
        })
    }
    async FetchData(){
    /* Function for fetching data */
        this.state.data = await this.orm.call('sale.order', 'get_data', [])
        this.state.lead_customer_data = await this.orm.call('sale.order','get_lead_customer', [])
        this.state.lead_product_data = await this.orm.call( 'sale.order', 'get_lead_product',[])
        this.state.lead_sale_data = await this.orm.call('sale.order','get_lead_order', [])
        this.state.lead_sale_team = await this.orm.call('sale.order','get_sales_team', [])
        this.state.least_sold = await this.orm.call('sale.order','get_least_sold', [])
        this.state.monthly_comparison = await this.orm.call('sale.order','get_my_monthly_comparison', [])
        this.chart(this.LeadCustomer.el,'doughnut',Object.keys(this.state.lead_customer_data.lead_templates),Object.values(this.state.lead_customer_data.lead_templates),)
        this.chart(this.LeadProducts.el,'doughnut',Object.keys(this.state.lead_product_data.lead_templates),Object.values(this.state.lead_product_data.lead_templates),)
        this.labeled_chart(this.LeadSaleOrders.el,'bar',Object.keys(this.state.lead_sale_data.lead_templates),'Sale Amount',Object.values(this.state.lead_sale_data.lead_templates),)
        this.chart(this.SalesTeamRevenue.el,'pie',Object.keys(this.state.lead_sale_team.lead_templates),Object.values(this.state.lead_sale_team.lead_templates),)
        this.labeled_chart(this.LeastSoldProduct.el,'bar',Object.keys(this.state.least_sold.lead_templates),'Product Count',Object.values(this.state.least_sold.lead_templates),)
        this.labeled_chart(this.MonthlyQuotation.el,'line',Object.keys(this.state.monthly_comparison.lead_templates),'Quotation Count',Object.values(this.state.monthly_comparison.lead_templates),)
    }
    async DateChanged(){
        this.state.data = await this.orm.call('sale.order', 'get_value', [this.state.date.start_date, this.state.date.end_date])
    }

    chart(canvas,type,labels,data){
        this.state.chart.push(new Chart(
            canvas,
            {
                type:type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                        data: data,
                        backgroundColor: [
                            'rgb(255,20,147)',
                            'rgb(186,85,211)',
                            'rgb(0,0,255)',
                            'rgb(0,191,255)',
                            'rgb(0,206,209)',
                            'rgb(32,178,170)',
                            'rgb(173,255,47)',
                            'rgb(205,92,92)',
                            'rgb(178,34,34)',
                            'rgb(0,128,128)',
                            ],
                        }
                    ]
                },
            }
        ))
    }
    labeled_chart(canvas,type,labels,label,data){
        this.state.chart.push(new Chart(
            canvas,
            {
                type:type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                        label: label,
                        data: data,
                        backgroundColor: [
                            'rgb(255,20,147)',
                            'rgb(186,85,211)',
                            'rgb(0,0,255)',
                            'rgb(0,191,255)',
                            'rgb(0,206,209)',
                            'rgb(32,178,170)',
                            'rgb(173,255,47)',
                            'rgb(205,92,92)',
                            'rgb(178,34,34)',
                            'rgb(0,128,128)',
                            ],
                        }
                    ]
                },
            }
        ))
    }
    on_dashboard_quotation_action(){
    /* Function for quotation dashboard */
        if (this.state.date.start_date && this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '>=', this.state.date.start_date], ['date_order', '<=', this.state.date.end_date]]
        }
        else if (this.state.date.start_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '>=', this.state.date.start_date]]
        }
        else if (this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'draft'], ['date_order', '<=', this.state.date.end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'draft']]
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: 'Quotations',
            res_model: 'sale.order',
            views: [[false, 'tree'], [false, 'form']],
            target: "current",
            domain: domain,
        });
    }
    on_dashboard_my_sale_order_action(){
    /* Function for Sale order dashboard */
        if (this.state.date.start_date && this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '>=', this.state.date.start_date], ['date_order', '<=', this.state.date.end_date]]
        }
        else if (this.state.date.start_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '>=', this.state.date.start_date]]
        }
        else if (this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sale'], ['date_order', '<=', this.state.date.end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sale']]
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: 'Sale Orders',
            res_model: 'sale.order',
            views: [[false, 'tree'], [false, 'form']],
            target: "current",
            domain: domain,
        });
    }
    on_dashboard_quotation_sent_action(){
    /* Function for Quotation sent dashboard */
        if (this.state.date.start_date && this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '>=', this.state.date.start_date], ['date_order', '<=', this.state.date.end_date]]
        }
        else if (this.state.date.start_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '>=', this.state.date.start_date]]
        }
        else if (this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sent'], ['date_order', '<=', this.state.date.end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['state', '=', 'sent']]
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: 'Quotations Sent',
            res_model: 'sale.order',
            views: [[false, 'tree'], [false, 'form']],
            target: "current",
            domain: domain,
        });
    }
    on_dashboard_quotation_cancel_action(){
    /* Function for Quotation Cancel dashboard */
        var domain = [['user_id', '=', session.uid], ['state', '=', 'cancel']]
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: 'Quotations Cancel',
            res_model: 'sale.order',
            views: [[false, 'tree'], [false, 'form']],
            target: "current",
            domain: domain,
        });
    }
    on_dashboard_customers_action(){
    /* Function for Customers dashboard */
        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Customers',
            res_model: 'res.partner',
            views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
            target: 'current',
        });
    }
    on_dashboard_products_action(){
    /* Function for Products dashboard */
        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Products',
            res_model: 'product.template',
            views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
            target: 'current',
        });
    }
    on_dashboard_to_invoice_action(){
    /* Function for To invoice dashboard */
        if (this.state.date.start_date && this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '>=', this.state.date.start_date], ['date_order', '<=', this.state.date.end_date]]
        }
        else if (this.state.date.start_date) {
            var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '>=', this.state.date.start_date]]
        }
        else if (this.state.date.end_date) {
            var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice'], ['date_order', '<=', this.state.date.end_date]]
        }
        else {
            var domain = [['user_id', '=', session.uid], ['invoice_status', '=', 'to invoice']]
        }
        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'To Invoice',
            res_model: 'sale.order',
            views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
            target: 'current',
            domain: domain,
        });
    }
}
SalesDashboard.template = "DashboardDashboard"
registry.category("actions").add('sale_dashboard', SalesDashboard)
