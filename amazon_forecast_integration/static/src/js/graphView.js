/** @odoo-module **/

/**
 * This module defines a custom Odoo web client action 'forecast'.
 * The action generates a scatter chart to display forecast data from the
   'amazon.dataset' model.
 * The chart represents forecast data for three points: p10, p50, and p90.
 */
import { registry } from '@web/core/registry';
const actionRegistry = registry.category("actions");
const { useRef, onMounted, useState } = owl;
import rpc from 'web.rpc';
import { browser } from '@web/core/browser/browser';
const { Component } = owl;

class ForecastReport extends Component{
    /**
     * It is responsible for initializing the component and its state.
     */
     setup(){
        super.setup(...arguments);
        this.forecastBarGraph = useRef("bubble-chart");
        this.FinalData = useState({
            ForecastData:[],
        })
        onMounted(async () =>{
            await this.forecastGraph();
        });
    }
    /**
     * The 'forecastGraph' function asynchronously retrieves forecast data from the 'amazon.dataset' model using RPC.
     * It then generates a scatter chart using the Chart.js library to visualize the data.
     */
    async forecastGraph(){
        let abc = await rpc.query({
            model:'amazon.dataset',
            method:'get_query_result',
        }).then(val => {
            this.FinalData.ForecastData = val
        });
            const { p10, p50, p90 } = this.FinalData.ForecastData
        function getMonthNameFromDate(dateString) {
            const date = new Date(dateString);
            const monthName = date.toLocaleString('default', { month: 'long' });
            return monthName;
        }
        const userDate = p10[0].Timestamp;
        const monthName = getMonthNameFromDate(userDate);
        let scatterChart = this.forecastBarGraph.el
        new Chart(scatterChart, {
            type: 'scatter',
            data: {
                datasets: [{
                label: 'Forecast in '+ monthName,
                data: [
                    { 'date': p10[0].Timestamp, 'demand': p10[0].Value },
                    { 'date': p50[0].Timestamp, 'demand': p50[0].Value},
                    { 'date': p90[0].Timestamp, 'demand': p90[0].Value}
                ],
                borderColor: 'rgb(0, 0, 255)',
                backgroundColor: 'rgba(0, 0, 255, 0.5)'
                }]
            },
            options: {
                parsing: {
                    xAxisKey: 'date',
                    yAxisKey: 'demand'
                },
                scales: {
                    y: {
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                        },
                        ticks: {
                            autoSkip: false,
                            stepSize: 1,
                        }
                    }
                }
            }
        });
    }
    goBack() {
//        this.trigger('back');
browser.history.go(-1)


    }
}
ForecastReport.template = "ForecastReport"
actionRegistry.add('forecast', ForecastReport);
