/** @odoo-module */
import { registry} from '@web/core/registry';
import { loadBundle } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted} = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
const { useRef } = owl;
export class PackersManagement extends Component {
        setup() {
              this.booking = useRef('BookingCanvas')
              this.truckAnalysis = useRef('CanvasTruck')
              this.distance = useRef('CanvasDistance')
              this.truckDistance = useRef('TruckDistance')
              this.CustWeight = useRef('CustomerWeight')
              this.TruckWeight = useRef('TruckWeight')
              this.Total = useRef('Total')
              this.TotalTwo = useRef('Total_two')
              this.TotalThree = useRef('Total_three')
              this.TotalFour = useRef('Total_four')
              this.BookingYear = useRef('BookingThisYear')
              this.BookingDay = useRef('BookingThisDay')
              this.BookingMonth = useRef('BookingThisMonth')
              this.BookingWeek = useRef('BookingThisWeek')
              this.DistanceYear = useRef('DistanceThisYear')
              this.DistanceMonth = useRef('DistanceThisMonth')
              this.DistanceDay = useRef('DistanceThisDay')
              this.DistanceWeek = useRef('DistanceThisWeek')
              this.InvoiceYear = useRef('InvoiceThisYear')
              this.InvoiceMonth = useRef('InvoiceThisMonth')
              this.InvoiceDay = useRef('InvoiceThisDay')
              this.InvoiceWeek = useRef('InvoiceThisWeek')
              this.AmountYear = useRef('AmountThisYear')
              this.AmountDay = useRef('AmountThisDay')
              this.AmountMonth = useRef('AmountThisMonth')
              this.AmountWeek = useRef('AmountThisWeek')
              this.action = useService('action')
            onWillStart(async () => await this.onWillStart());
            onMounted(() => {
            this.onclick_this_month('month')
        });
        }

//   Filtering by date
	stock_selection(e){
        e.stopPropagation();
         var value = e.target.value;
        if (value=="year"){
            this.onclick_this_year(value);
        }else if (value=="day"){
            this.onclick_this_day(value);
        }else if (value=="month"){
            this.onclick_this_month(value);
        }else if (value=="week"){
            this.onclick_this_week(value);
        }
    }

    async onWillStart() {
       // returns the function fetch_data when page load.
       var self = this;
       return self.fetch_data();
    }
    fetch_data() {//function to call rpc query to fetch data fom python
       self = this;
       var def1 =  rpc('/web/dataset/call_kw/truck.booking/get_total_booking',{
           model: 'truck.booking',
           method: 'get_total_booking',
           args:{},
           kwargs:{}
       }).then(function(result)
        {
          self.booking_count = result.total_booking,
          self.distance_count = result.total_distance_count,
          self.total_invoice = result.total_invoice
          self.total_amount = result.total_amount
        });
       var def2 =  rpc('/web/dataset/call_kw/truck.booking/get_top_truck',{
           model: 'truck.booking',
           method: 'get_top_truck',
           args:{},
           kwargs:{}
       }).then(function(result)
        {
        self.truck = result['truck']
        self.customer = result['customer']
        self.upcoming = result['upcoming']
         });
         return Promise.all([def1, def2]);
    }

    render_booking (){//Function to add booking chart on the basis of customer
        self = this;
        rpc('/web/dataset/call_kw/truck.booking/get_booking_analysis',{
            model: "truck.booking",
            method: "get_booking_analysis",
            args:{},
           kwargs:{}
        }).then(function (result) {
            new Chart(self.booking.el, {
                type: 'bar',
                data: {
                    labels: result.name,
                    datasets: [{
                        label: 'Count',
                        data: result.count,
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
        });
    }

    render_weight(){//Function to add total goods weight chart on the basis of customer and truck
        rpc('/web/dataset/call_kw/truck.booking/get_weight',{
            model: "truck.booking",
            method: "get_weight",
           args:{},
           kwargs:{}
        }).then(function (result) {
             new Chart(self.CustWeight.el, {
                        type: 'line',
                    data: {
                        labels: result.cust,
                        datasets: [{
                            label: 'count',
                            data: result.cust_sum,
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
                        maintainAspectRatio: false,
                    }
                    });
             new Chart(self.CustWeight.el, {
                type: 'bar',
                data: {
                    labels: result.truck_name,
                    datasets: [{
                        label: 'Count',
                        data: result.truck_sum,
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
                    maintainAspectRatio: false,
                }
            });
        });
    }

    render_truck(){//Function to add booking chart on the basis of truck
        rpc('/web/dataset/call_kw/truck.booking/get_truck_analysis',{
            model: "truck.booking",
            method: "get_truck_analysis",
            args:{},
            kwargs:{}
        }).then(function (result) {
            new Chart(self.truckAnalysis.el, {
                type: 'doughnut',
                data: {
                    labels: result.name,
                    datasets: [{
                        label: 'Count',
                        data: result.count,
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
        });
    }

    render_distance(){//Function to add total distance chart on the basis of customer and truck
         rpc('/web/dataset/call_kw/truck.booking/get_distance',{
            model: "truck.booking",
            method: "get_distance",
            args:{},
            kwargs:{}
         }).then(function (result) {
            new Chart(self.distance.el, {
                type: 'doughnut',
                data: {
                    labels: result.cust,
                    datasets: [{
                        label: 'Count',
                        data: result.cust_sum,
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
            new Chart(self.truckDistance.el, {
                        type: 'line',
                    data: {
                        labels: result.truck_name,
                        datasets: [{
                            label: 'count',
                            data: result.truck_sum,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
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
            });
    }

    onclick_this_week (ev) {//Function shows week filtered dashboard.
            self = this;
            rpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                 document.querySelectorAll('.total').forEach(function(el) {
                 el.style.display = 'none';
                });
                document.getElementById('booking_this_month').style.display = 'none';
                document.getElementById('distance_this_month').style.display = 'none';
                document.getElementById('amount_this_month').style.display = 'none';
                document.getElementById('invoice_this_month').style.display = 'none';
                document.getElementById('booking_this_year').style.display = 'none';
                document.getElementById('distance_this_year').style.display = 'none';
                document.getElementById('amount_this_year').style.display = 'none';
                document.getElementById('invoice_this_year').style.display = 'none';
                document.getElementById('booking_this_day').style.display = 'none';
                document.getElementById('amount_this_day').style.display = 'none';
                document.getElementById('invoice_this_day').style.display = 'none';
                document.getElementById('distance_this_day').style.display = 'none';
                document.getElementById('booking_this_week').style.display = 'block';
                document.getElementById('distance_this_week').style.display = 'block';
                document.getElementById('amount_this_week').style.display = 'block';
                document.getElementById('invoice_this_week').style.display = 'block';
                 self.BookingWeek.el.innerHTML = '';
                 self.DistanceWeek.el.innerHTML = '';
                 self.InvoiceWeek.el.innerHTML = '';
                 self.AmountWeek.el.innerHTML = '';
                 var spanElement_1 = document.createElement('span');
                 spanElement_1.innerHTML = result['booking'][0]['count'] || 0;
                 self.BookingWeek.el.appendChild(spanElement_1);
                  var spanElement_2 = document.createElement('span');
                 spanElement_2.innerHTML = result['distance'][0]['sum']|| 0;
                 self.DistanceWeek.el.appendChild(spanElement_2);
                  var spanElement_3 = document.createElement('span');
                 spanElement_3.innerHTML = result['amount'][0]['sum'] || 0;
                 self.AmountWeek.el.appendChild(spanElement_3);
                  var spanElement_4 = document.createElement('span');
                 spanElement_4.innerHTML = result['invoice'][0]['sum'] || 0;
                 self.InvoiceWeek.el.appendChild(spanElement_4);
                 self.get_cust_invoice(result);
                 self.get_truck_invoice(result);
                 self.get_cust_distance(result);
                 self.get_truc_distance(result);
                 self.get_cust_weight(result);
                 self.get_truck_weight(result);
              })
    }

    onclick_this_day(ev) {//Function shows day filtered dashboard.
            self = this;
            rpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                   document.querySelectorAll('.total').forEach(function(el) {
                   el.style.display = 'none';
                    });
                  document.getElementById('booking_this_month').style.display = 'none';
                  document.getElementById('distance_this_month').style.display = 'none';
                  document.getElementById('amount_this_month').style.display = 'none';
                  document.getElementById('invoice_this_month').style.display = 'none';
                  document.getElementById('booking_this_week').style.display = 'none';
                  document.getElementById('distance_this_week').style.display = 'none';
                  document.getElementById('amount_this_week').style.display = 'none';
                  document.getElementById('invoice_this_week').style.display = 'none';
                 document.getElementById('booking_this_year').style.display = 'none';
                 document.getElementById('distance_this_year').style.display = 'none';
                 document.getElementById('amount_this_year').style.display = 'none';
                 document.getElementById('invoice_this_year').style.display = 'none';
                 document.getElementById('booking_this_day').style.display = 'block';
                 document.getElementById('amount_this_day').style.display = 'block';
                 document.getElementById('invoice_this_day').style.display = 'block';
                 document.getElementById('distance_this_day').style.display = 'block';
                 self.BookingDay.el.innerHTML = '';
                 self.DistanceDay.el.innerHTML = '';
                 self.AmountDay.el.innerHTML = '';
                 self.InvoiceDay.el.innerHTML = '';
                 var spanElement_1 = document.createElement('span');
                 spanElement_1.innerHTML = result['booking'][0]['count'];
                 self.BookingDay.el.appendChild(spanElement_1);
                  var spanElement_2 = document.createElement('span');
                 spanElement_2.innerHTML = result['distance'][0]['sum'];
                 self.DistanceDay.el.appendChild(spanElement_2);
                  var spanElement_3 = document.createElement('span');
                 spanElement_3.innerHTML = result['amount'][0]['sum'] || 0;
                 self.AmountDay.el.appendChild(spanElement_3);
                  var spanElement_4 = document.createElement('span');
                 spanElement_4.innerHTML = result['invoice'][0]['sum'] || 0;
                 self.InvoiceDay.el.appendChild(spanElement_4);
                 self.get_cust_invoice(result);
                 self.get_truck_invoice(result);
                 self.get_cust_distance(result);
                 self.get_truc_distance(result);
                 self.get_cust_weight(result);
                 self.get_truck_weight(result);
            })
    }

    onclick_this_year(ev) {
    //Function shows a year filtered dashboard
            self = this;
            rpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
                model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                document.getElementById('booking_this_day').style.display = 'none';
                document.getElementById('amount_this_day').style.display = 'none';
                document.getElementById('invoice_this_day').style.display = 'none';
                document.getElementById('booking_this_month').style.display = 'none';
                document.getElementById('distance_this_month').style.display = 'none';
                document.getElementById('amount_this_month').style.display = 'none';
                document.getElementById('invoice_this_month').style.display = 'none';
                document.getElementById('booking_this_week').style.display = 'none';
                document.getElementById('distance_this_week').style.display = 'none';
                document.getElementById('amount_this_week').style.display = 'none';
                document.getElementById('invoice_this_week').style.display = 'none';
                document.getElementById('booking_this_year').style.display = 'block';
                document.getElementById('distance_this_year').style.display = 'block';
                document.getElementById('amount_this_year').style.display = 'block';
                document.getElementById('invoice_this_year').style.display = 'block';
                document.getElementById('booking_this_year').style.display = 'block';
                 document.querySelectorAll('.total').forEach(function(el) {
                        el.style.display = 'none';
                    });
                 self.BookingYear.el.innerHTML = '';
                 self.DistanceYear.el.innerHTML = '';
                 self.AmountYear.el.innerHTML = '';
                 self.InvoiceYear.el.innerHTML = '';
                    var spanElement_booking = document.createElement('span');
                    spanElement_booking.innerHTML = result['booking'][0]['count'];
                    self.BookingYear.el.appendChild(spanElement_booking);
                    var spanElement_distance = document.createElement('span');
                    spanElement_distance.innerHTML = result['distance'][0]['sum'];
                    self.DistanceYear.el.appendChild(spanElement_distance);
                    var spanElement_amount = document.createElement('span');
                    spanElement_amount.innerHTML = result['amount'][0]['sum'];
                    self.AmountYear.el.appendChild(spanElement_amount);
                    var spanElement_invoice = document.createElement('span');
                    spanElement_invoice.innerHTML = result['invoice'][0]['sum'] || 0;
                    self.InvoiceYear.el.appendChild(spanElement_invoice);
                    self.get_cust_invoice(result);
                    self.get_truck_invoice(result);
                    self.get_cust_distance(result);
                    self.get_truc_distance(result);
                    self.get_cust_weight(result);
                    self.get_truck_weight(result);
            })
    }
    onclick_this_month(ev) {//Function shows month filtered dashboard.
            self = this;
            rpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
               method: 'get_select_filter',
               args: [ev],
               kwargs:{}
            })
            .then(function (result) {
                document.querySelectorAll('.total').forEach(function(el) {
                el.style.display = 'none';
               });
                 document.getElementById('booking_this_year').style.display = 'none';
                document.getElementById('distance_this_year').style.display = 'none';
                document.getElementById('amount_this_year').style.display = 'none';
                document.getElementById('invoice_this_year').style.display = 'none';
                document.getElementById('booking_this_day').style.display = 'none';
                document.getElementById('amount_this_day').style.display = 'none';
                document.getElementById('invoice_this_day').style.display = 'none';
                document.getElementById('distance_this_day').style.display = 'none';
                document.getElementById('booking_this_week').style.display = 'none';
                document.getElementById('distance_this_week').style.display = 'none';
                document.getElementById('amount_this_week').style.display = 'none';
                document.getElementById('invoice_this_week').style.display = 'none';
                document.getElementById('booking_this_month').style.display = 'block';
                document.getElementById('distance_this_month').style.display = 'block';
                document.getElementById('amount_this_month').style.display = 'block';
                document.getElementById('invoice_this_month').style.display = 'block';
                 self.BookingMonth.el.innerHTML = '';
                 self.DistanceMonth.el.innerHTML = '';
                 self.AmountMonth.el.innerHTML = '';
                 self.InvoiceMonth.el.innerHTML = '';
                var spanElement_1 = document.createElement('span');
                spanElement_1.innerHTML = result['booking'][0]['count'];
                self.BookingMonth.el.appendChild(spanElement_1);
                var spanElement_2 = document.createElement('span');
                spanElement_2.innerHTML = result['distance'][0]['sum'];
                self.DistanceMonth.el.appendChild(spanElement_2);
                var spanElement_3 = document.createElement('span');
                spanElement_3.innerHTML = result['amount'][0]['sum']|| 0;
                self.AmountMonth.el.appendChild(spanElement_3);
                var spanElement_4 = document.createElement('span');
                spanElement_4.innerHTML = result['invoice'][0]['sum'] || 0;;
                self.InvoiceMonth.el.appendChild(spanElement_4);
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        }
    get_cust_invoice(result) {
        //function to create a chart which shows the total invoice according to the customer
         new Chart(document.getElementById("booking"), {
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
                            minBarThickness:6,
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

    get_truck_invoice(result){//function to create a chart which shows the total invoice according to the truck.
          new Chart(document.getElementById("truck"), {
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

    get_cust_distance(result){//function to create a graph which shows the distance according to the customer
       new Chart(document.getElementById("cust_distance"), {
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

    get_truc_distance(result){//function to create a graph which shows the distance according to the truck
        new Chart(document.getElementById("truck_distance"), {
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

    get_cust_weight(result){//function to create a chart which shows the total goods weight according to the customer
        new Chart(document.getElementById("cust_weight"), {
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

    get_truck_weight (result){//function to create a chart which shows the total goods weight according to the truck
       new Chart(document.getElementById("truck_weight"), {
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
registry.category("actions").add("dash_tags", PackersManagement)
