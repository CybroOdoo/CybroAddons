import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, signal } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class PackersManagement extends Component {
    setup() {
        this.upcoming = [];
        this.customer = [];
        this.truck = [];
        this.booking_count = 0;
        this.distance_count = 0;
        this.total_invoice = 0;
        this.total_amount = 0;
        this.booking = signal.ref();
        this.truckAnalysis = signal.ref();
        this.distance = signal.ref();
        this.truckDistance = signal.ref();
        this.CustWeight = signal.ref();
        this.TruckWeight = signal.ref();
        this.Total = signal.ref();
        this.TotalTwo = signal.ref();
        this.TotalThree = signal.ref();
        this.TotalFour = signal.ref();
        this.BookingYear = signal.ref();
        this.BookingDay = signal.ref();
        this.BookingMonth = signal.ref();
        this.BookingWeek = signal.ref();
        this.DistanceYear = signal.ref();
        this.DistanceMonth = signal.ref();
        this.DistanceDay = signal.ref();
        this.DistanceWeek = signal.ref();
        this.InvoiceYear = signal.ref();
        this.InvoiceMonth = signal.ref();
        this.InvoiceDay = signal.ref();
        this.InvoiceWeek = signal.ref();
        this.AmountYear = signal.ref();
        this.AmountDay = signal.ref();
        this.AmountMonth = signal.ref();
        this.AmountWeek = signal.ref();
        this.action = useService('action');
        this.charts = {};
        onWillStart(async () => await this.onWillStart());
        onMounted(() => {
            this.onclick_this_month('month');
        });
    }

    renderChart(elementId, config) {
        const canvas = typeof elementId === 'string' ? document.getElementById(elementId) : elementId;
        if (!canvas) {
            return null;
        }
        const key = typeof elementId === 'string' ? elementId : (canvas.id || 'chart');
        if (this.charts && this.charts[key]) {
            this.charts[key].destroy();
            delete this.charts[key];
        }
        if (typeof Chart.getChart === 'function') {
            const existing = Chart.getChart(canvas);
            if (existing) {
                existing.destroy();
            }
        }
        this.charts = this.charts || {};
        this.charts[key] = new Chart(canvas, config);
        return this.charts[key];
    }

    //   Filtering by date
    stock_selection(e) {
        e.stopPropagation();
        var value = e.target.value;
        if (value == "year") {
            this.onclick_this_year(value);
        } else if (value == "day") {
            this.onclick_this_day(value);
        } else if (value == "month") {
            this.onclick_this_month(value);
        } else if (value == "week") {
            this.onclick_this_week(value);
        }
    }

    async onWillStart() {
        // returns the function fetch_data when page load.
        return this.fetch_data();
    }
    fetch_data() {//function to call rpc query to fetch data fom python
        const self = this;
        var def1 = rpc('/web/dataset/call_kw/truck.booking/get_total_booking', {
            model: 'truck.booking',
            method: 'get_total_booking',
            args: {},
            kwargs: {}
        }).then(function (result) {
            self.booking_count = result.total_booking,
                self.distance_count = result.total_distance_count,
                self.total_invoice = result.total_invoice
            self.total_amount = result.total_amount
        });
        var def2 = rpc('/web/dataset/call_kw/truck.booking/get_top_truck', {
            model: 'truck.booking',
            method: 'get_top_truck',
            args: {},
            kwargs: {}
        }).then(function (result) {
            self.truck = result['truck'] || [];
            self.customer = result['customer'] || [];
            self.upcoming = result['upcoming'] || [];
        });
        return Promise.all([def1, def2]);
    }


    applyFilter(period) {
        const self = this;
        return rpc('/web/dataset/call_kw/truck.booking/get_select_filter', {
            model: 'truck.booking',
            method: 'get_select_filter',
            args: [period],
            kwargs: {}
        }).then(function (result) {
            if (!result) {
                return;
            }
            const periods = ['day', 'week', 'month', 'year'];
            document.querySelectorAll('.total').forEach(function (el) {
                el.style.display = 'none';
            });
            periods.forEach(function (p) {
                ['booking', 'distance', 'amount', 'invoice'].forEach(function (metric) {
                    const el = document.getElementById(`${metric}_this_${p}`);
                    if (el) {
                        el.style.display = p === period ? 'block' : 'none';
                    }
                });
            });

            const bookingCount = (result['booking'] && result['booking'][0] && result['booking'][0]['count']) || 0;
            const distanceSum = (result['distance'] && result['distance'][0] && result['distance'][0]['sum']) || 0;
            const amountSum = (result['amount'] && result['amount'][0] && result['amount'][0]['sum']) || 0;
            const invoiceSum = (result['invoice'] && result['invoice'][0] && result['invoice'][0]['sum']) || 0;

            const periodName = period.charAt(0).toUpperCase() + period.slice(1);
            const bookingRef = self[`Booking${periodName}`];
            const distanceRef = self[`Distance${periodName}`];
            const amountRef = self[`Amount${periodName}`];
            const invoiceRef = self[`Invoice${periodName}`];

            if (bookingRef && typeof bookingRef === 'function' && bookingRef()) {
                bookingRef().innerHTML = `<span>${bookingCount}</span>`;
            }
            if (distanceRef && typeof distanceRef === 'function' && distanceRef()) {
                distanceRef().innerHTML = `<span>${distanceSum}</span>`;
            }
            if (amountRef && typeof amountRef === 'function' && amountRef()) {
                amountRef().innerHTML = `<span>${amountSum}</span>`;
            }
            if (invoiceRef && typeof invoiceRef === 'function' && invoiceRef()) {
                invoiceRef().innerHTML = `<span>${invoiceSum}</span>`;
            }

            self.get_cust_invoice(result);
            self.get_truck_invoice(result);
            self.get_cust_distance(result);
            self.get_truc_distance(result);
            self.get_cust_weight(result);
            self.get_truck_weight(result);
        });
    }

    onclick_this_week(ev) {
        return this.applyFilter('week');
    }

    onclick_this_day(ev) {
        return this.applyFilter('day');
    }

    onclick_this_year(ev) {
        return this.applyFilter('year');
    }

    onclick_this_month(ev) {
        return this.applyFilter('month');
    }
    get_cust_invoice(result) {
        //function to create a chart which shows the total invoice according to the customer
        this.renderChart("booking", {
            type: 'bar',
            data: {
                labels: result.cust_invoice_name,
                datasets: [{
                    label: 'Count',
                    data: result.cust_invoice_sum,
                    backgroundColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarThickness: 6,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'bar',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }

    get_truck_invoice(result) {//function to create a chart which shows the total invoice according to the truck.
        this.renderChart("truck", {
            type: 'doughnut',
            data: {
                labels: result.truck_invoice_name,
                datasets: [{
                    label: 'Count',
                    data: result.truck_invoice_count,
                    backgroundColor: [
                        "#665191",
                        "#ff7c43",
                        "#ffa600",
                        "#d45087",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF",
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'pie',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }

    get_cust_distance(result) {//function to create a graph which shows the distance according to the customer
        this.renderChart("cust_distance", {
            type: 'doughnut',
            data: {
                labels: result.cust_distance_name,
                datasets: [{
                    label: 'Count',
                    data: result.cust_distance_count,
                    backgroundColor: [
                        "#665191",
                        "#ff7c43",
                        "#ffa600",
                        "#d45087",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF",
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'pie',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }

    get_truc_distance(result) {//function to create a graph which shows the distance according to the truck
        this.renderChart("truck_distance", {
            type: 'line',
            data: {
                labels: result.truck_distance_name,
                datasets: [{
                    label: 'count',
                    data: result.truck_distance_count,
                    backgroundColor: '#003f5c',
                    borderColor: '#003f5c',
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'line',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }

    get_cust_weight(result) {//function to create a chart which shows the total goods weight according to the customer
        this.renderChart("cust_weight", {
            type: 'line',
            data: {
                labels: result.cust_weight_name,
                datasets: [{
                    label: 'count',
                    data: result.cust_weight_count,
                    backgroundColor: '#003f5c',
                    borderColor: '#003f5c',
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'line',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }

    get_truck_weight(result) {//function to create a chart which shows the total goods weight according to the truck
        this.renderChart("truck_weight", {
            type: 'bar',
            data: {
                labels: result.truck_weight_name,
                datasets: [{
                    label: 'Count',
                    data: result.truck_weight_count,
                    backgroundColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#6d5c16",
                        "#CCCCFF"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    type: 'bar',
                    fill: false
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    },
                },
                responsive: true,
            }
        });
    }
}
PackersManagement.template = "PackersMoversDashBoard"
registry.category("actions").add("packers_movers_dashboard_tags", PackersManagement)
