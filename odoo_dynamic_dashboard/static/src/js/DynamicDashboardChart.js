/** @odoo-module */

import { registry} from '@web/core/registry';
import { loadJS} from '@web/core/assets';
import { getColor } from "@web/core/colors/colors";
const { Component, xml, onWillStart, useRef, onMounted } = owl

export class DynamicDashboardChart extends Component {
    setup() {
        this.doAction = this.props.doAction.doAction
        this.chartRef = useRef("chart")
        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
        })
        onMounted(()=> this.renderChart())
    }
    renderChart(){
        if (this.props.widget.graph_type){
            const x_axis = this.props.widget.x_axis
            const y_axis = this.props.widget.y_axis
            const data = []
            for (let i = 0; i < x_axis.length; i++) {
                const value = { key: x_axis[i], value: y_axis[i] }
                data.push(value);
            }
            new Chart(
                this.chartRef.el,
                    {
                      type: this.props.widget.graph_type || 'bar',
                          data: {
                            labels: data.map(row => row.key),
                                datasets: [
                                  {
                                    label: this.props.widget.measured_field,
                                    data: data.map(row => row.value),
                                    backgroundColor: data.map((_, index) => getColor(index)),
                                    hoverOffset : 4
                                  }
                                ]
                          },
                    }
              );
        }
    }
    async getConfiguration(){
        var id = this.props.widget.id
        await this.doAction({
              type: 'ir.actions.act_window',
              res_model: 'dashboard.block',
              res_id: id,
              view_mode: 'form',
              views: [[false, "form"]]
          });
    }
}
DynamicDashboardChart.template = xml `
<div style="padding-bottom:30px" t-att-class="this.props.widget.cols +' col-4 block'" t-att-data-id="this.props.widget.id">
    <div class="card">
        <div class="card-header">
            <div class="row">
                <div class="col">
                        <h3><t t-esc="this.props.widget.name"/></h3>
                </div>
                <div class="col">
                    <div style="float:right;"><i title="Configuration" class="fa fa-cog block_setting fa-2x cursor-pointer" t-on-click="getConfiguration"/></div>
                </div>
            </div>
        </div>
        <div class="card-body" id="in_ex_body_hide">
            <div class="row">
                <div class="col-md-12 chart_canvas">
                    <div id="chart_canvas">
                        <canvas t-ref="chart"/>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`


