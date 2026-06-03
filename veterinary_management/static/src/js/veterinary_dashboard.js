/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted, onWillStart,  useRef, useState } = owl
const actionRegistry = registry.category("actions");

class VeterinaryDashboard extends Component {
    setup() {
        this.state = useState({
            data: {},
            data_grooming: {},
            data_medicine: {},
            chart: [],
            countData: {},
        })
         this.orm = useService('orm')
         this.monthlyAppointments = useRef("chart")
         this.topGroomingProducts = useRef("top_grooming_products")
         this.topMedicines = useRef("top_medicines")
         onWillStart(async () =>{
         await this._fetch_data();
         })
         onMounted(async () =>{
         this.renderChart();
         })
   }
   async _fetch_data(){
   var self = this;
  this.state.data = await this.orm.call("res.patient" , "get_monthly_appointments", [{}]);
  this.state.data_grooming = await this.orm.call("animal.grooming" , "get_top_grooming_products", [{}]);
  this.state.data_medicine = await this.orm.call("prescription.orders" , "get_top_medicines", [{}]);
  const countData = await this.orm.call("res.patient", "get_count_data", [], {});
        this.state.countData = {
            totalGrooming: countData.total_grooming,
            totalProcedure: countData.total_procedure,
            totalTraining: countData.total_training,
            totalDoctors: countData.total_doctors,
            totalNurses: countData.total_nurses,
            totalSurgeries: countData.total_surgeries,
            todayGrooming: countData.today_grooming,
            todayProcedure: countData.today_procedure,
            todayTraining: countData.today_training,
            todayDoctors: countData.today_doctors,
            todayNurses: countData.today_nurses,
            todaySurgeries: countData.today_surgeries,
        };
       };
       async renderChart(){
       this.charts(this.monthlyAppointments.el,'bar',this.state.data['products'],'MonthlyAppoitment',this.state.data['count'])
       this.charts(this.topGroomingProducts.el,'pie',this.state.data_grooming['products'],'TopGroomingProducts',this.state.data_grooming['counts'])
       this.charts(this.topMedicines.el,'pie',this.state.data_medicine['products'],'TopMedicines',this.state.data_medicine['counts'])
       }
 charts(canvas,type,labels,label,data){
/* Function for passing datas to the charts */
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
                    }
                ]
            },
        }
    ))
}
}

VeterinaryDashboard.template = "veterinary_management.VeterinaryDashboard";
actionRegistry.add("veterinary_dashboard_tag", VeterinaryDashboard);
