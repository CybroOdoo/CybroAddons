/** @odoo-module */
import { registry } from "@web/core/registry"
import { loadJS} from '@web/core/assets';
import { useService } from "@web/core/utils/hooks"
const { Component, useRef, onMounted ,useState , onWillStart} = owl

export class AccountDashboard extends Component {
    setup(){
        this.state = useState({
            data:{},
            top:{},
            income_chart:{},
            chart:[],
            payment_data: [],
            top_sale_cust: [],
            IncomeExpense:'income',
            top_filter: 'this_month',
            income:'income_this_month',
            aged_filter: 'aged_receive',
            top_sale_cust_filter: 'this_month',
            aged_payable_filter: 'this_month',
            payment_data_filter: 'this_month',
            payment_list_filter: 'customer_payment',
        })
        this.All = useRef("All"),
        this.AgedRecords = useRef("AgedRecords"),
        this.Balance = useRef("Balance"),
        this.orm = useService("orm");
        onWillStart(async () => {
            await this.FetchData();
        })
        onMounted(async() => {
            this.RenderChart()
        })
    }
    async onPeriodChange(){
        if (this.state.chart.length !=0) {
            this.state.chart.forEach((chart)=> {
                chart.destroy()
            })
            this.FetchData()
        }
    }
    async FetchData(){
        this.state.data = await this.orm.call('account.move','get_datas',[]);
        this.state.income_chart = await this.orm.call("account.move","get_income_chart", [this.state.income]);
        this.state.payment_data = await this.orm.call("account.move","get_payment_data", [this.state.payment_list_filter, this.state.payment_data_filter]);
        this.state.top = await this.orm.call("account.move","get_top_datas", [this.state.top_filter]);
        this.state.aged_payable = await this.orm.call("account.move","get_aged_payable", [this.state.aged_filter,this.state.aged_payable_filter]);
        this.state.top_sale_cust = await this.orm.call("account.move","get_sale_revenue", [this.state.top_sale_cust_filter]);
        this.state.balance = await this.orm.call("account.move","get_bank_balance", []);
        this.RenderChart()
    }
    async RenderChart(){
        this.aged_chart(this.AgedRecords.el,'bar',this.state.aged_payable.partner,'Amount',this.state.aged_payable.amount)
        if (this.state.IncomeExpense == 'income'){
            this.income_charts(this.All.el,'bar',this.state.income_chart.date,this.state.income_chart.income)
        }
        else if (this.state.IncomeExpense == 'expense'){
            this.expense_charts(this.All.el,'bar',this.state.income_chart.date,this.state.income_chart.expense)
        }
        else if (this.state.IncomeExpense == 'profit'){
            this.profit_charts(this.All.el,'line',this.state.income_chart.date,this.state.income_chart.profit)
        }
        else {
            this.AllInOneChart(this.All.el,'bar',this.state.income_chart.date,this.state.income_chart.income,this.state.income_chart.expense,this.state.income_chart.profit)
        }
    }
    aged_chart(canvas,type,labels,label,data){
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
                        borderRadius: 10,
                        backgroundColor: 'rgba(39, 232, 232, 0.5)',
                        borderColor: 'rgba(39, 232, 232, 1)',
                        }
                    ]
                },
            }
        ))
    }
    income_charts(canvas,type,labels,data){
        this.state.chart.push(new Chart(
            canvas,
            {
                type: type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data,
                            borderWidth: 2,
                            borderRadius: 10,
                            borderSkipped: false,
                            backgroundColor: 'rgba(39, 232, 232, 0.5)',
                            borderColor: 'rgba(39, 232, 232, 1)',
                        },
                    ]
                },
                }
        ));
    };
    expense_charts(canvas,type,labels,expense){
        this.state.chart.push(new Chart(
            canvas,
            {
                type: type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Expense',
                            data: expense,
                            type: type === 'bar' ? 'polarArea' : 'bar',
                        },
                    ]
                },
            }
        ));
    };
    profit_charts(canvas,type,labels,profit){
        this.state.chart.push(new Chart(
            canvas,
            {
                type: type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Profit/Loss',
                            data: profit,
                            fill: true,
                            borderColor: 'rgba(245, 65, 10, 1)',
                        },
                    ]
                },
            }
        ));
    };
    AllInOneChart(canvas,type,labels,data,expense,profit){
        this.state.chart.push(new Chart(
            canvas,
            {
                type: type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data,
                            type: type === 'line' ? 'line' : 'bar',
                            backgroundColor: 'rgba(39, 232, 232, 0.5)',
                            borderColor: 'rgba(39, 232, 232, 1)',
                        },
                        {
                            label: 'Expense',
                            data: expense,
                            type: type === 'bar' ? 'radar' : 'bar',
                            backgroundColor: 'rgba(0, 0, 0, 0.5)',
                            borderColor: 'rgba(0, 0, 0, 1)',
                        },
                        {
                            label: 'Profit/Loss',
                            data: profit,
                            type: 'line',
                            fill: false,
                            borderColor: 'rgba(245, 65, 10, 1)',
                        },
                    ]
                },
            }
        ));
    };
}
AccountDashboard.template = "AccountDashboard"
registry.category("actions").add('accounting_dashboard_tags', AccountDashboard)
