/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"
const { Component, onMounted, onWillStart,  useRef, useState } = owl

export class StorageDashboard extends Component {
/*  Extending component and creating class StorageDashboard */
    setup(){
        this.state = useState({
            data:{},
            chart_data:{},
        })
        this.orm = useService("orm");
        this.StorageChart = useRef("StorageChart");
        onWillStart(async () => {
                await this.FetchData()
            });
        onMounted(async() => {
            this.RenderChart()
        });

    }
    async FetchData(){
    /* Fetch datas for chart and table */
        this.state.data = await this.orm.call('storage.usage', 'get_info', [])
        this.state.chart_data = await this.orm.call('storage.usage', 'get_data', [])
    }
    async RenderChart(){
    /* Function for rendering the chart with fetched datas */
        this.charts(this.StorageChart.el,'bar',this.state.chart_data.x_data,'Size Used In MB',this.state.chart_data.y_data)
    }

    charts(canvas,type,labels,label,data){
        new Chart(
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
        )
    }
}
StorageDashboard.template = "DashboardDashboard"
registry.category("actions").add('storage_dashboard_tag', StorageDashboard)
