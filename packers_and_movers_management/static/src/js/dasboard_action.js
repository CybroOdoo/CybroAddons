/** @odoo-module */
import { registry} from '@web/core/registry';
import { loadBundle } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted} = owl
import { jsonrpc } from "@web/core/network/rpc_service";
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

	stock_selection(e){
        e.stopPropagation();
        var value = $(e.target).val();
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


       async onWillStart() {// returns the function fetch_data when page load.
       var self = this;
       return $.when(loadBundle(this)).then(function() {
           return self.fetch_data()
           ;
            });
        }

       fetch_data() {//function to call rpc query to fetch data fom python
       self = this;
       var def1 =  jsonrpc('/web/dataset/call_kw/truck.booking/get_total_booking',{
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
       var def2 =  jsonrpc('/web/dataset/call_kw/truck.booking/get_top_truck',{
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
       return $.when(def1,def2);
   }

       render_booking (){//Function to add booking chart on the basis of customer
        self = this;
        jsonrpc('/web/dataset/call_kw/truck.booking/get_booking_analysis',{
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
        jsonrpc('/web/dataset/call_kw/truck.booking/get_weight',{
            model: "truck.booking",
            method: "get_weight",
           args:{},
           kwargs:{}
        }).then(function (result) {
             new Chart(self.CustWeight.el, {
                        type: 'line',
                    data: {
                        labels: result.cust,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.cust_sum, // Specify the data values array
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
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
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
        jsonrpc('/web/dataset/call_kw/truck.booking/get_truck_analysis',{
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
    jsonrpc('/web/dataset/call_kw/truck.booking/get_distance',{
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
                    labels: result.truck_name,//x axis
                    datasets: [{
                        label: 'count', // Name the series
                        data: result.truck_sum, // Specify the data values array
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
                    responsive: true, // Instruct chart js to respond nicely.
                }
                });
        });
    }

    onclick_this_week (ev) {//Function shows week filtered dashboard.
            self = this;
            jsonrpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                $('.total').hide();
                $('#booking_this_month').hide();
                $('#distance_this_month').hide();
                $('#amount_this_month').hide();
                $('#invoice_this_month').hide();
                $('#booking_this_year').hide();
                $('#distance_this_year').hide();
                $('#amount_this_year').hide();
                $('#invoice_this_year').hide();
                $('#booking_this_day').hide();
                $('#distance_this_day').hide();
                $('#amount_this_day').hide();
                $('#invoice_this_day').hide();
                $('#booking_this_week').show();
                $('#distance_this_week').show();
                $('#amount_this_week').show();
                $('#invoice_this_week').show();
                $(self.BookingWeek.el).empty();
                $(self.DistanceWeek.el).empty();
                $(self.InvoiceWeek.el).empty();
                $(self.AmountWeek.el).empty();
                $(self.BookingWeek.el).append('<span>' + result['booking'][0]['count'] + '</span>');
                $(self.DistanceWeek.el).append('<span>' + (result['distance'][0]['sum'] || 0) + '</span>');
                $(self.AmountWeek.el).append('<span>' + (result['amount'][0]['sum'] || 0) + '</span>');
                $(self.InvoiceWeek.el).append('<span>' + (result['invoice'][0]['sum'] || 0) + '</span>');
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
            jsonrpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                $('.total').hide();
                $('#booking_this_month').hide();
                $('#distance_this_month').hide();
                $('#amount_this_month').hide();
                $('#invoice_this_month').hide();
                $('#booking_this_week').hide();
                $('#distance_this_week').hide();
                $('#amount_this_week').hide();
                $('#invoice_this_week').hide();
                $('#booking_this_year').hide();
                $('#distance_this_year').hide();
                $('#amount_this_year').hide();
                $('#invoice_this_year').hide();
                $('#booking_this_day').show();
                $('#distance_this_day').show();
                $('#amount_this_day').show();
                $('#invoice_this_day').show();
                $(self.BookingDay.el).empty();
                $(self.DistanceDay.el).empty();
                $(self.AmountDay.el).empty();
                $(self.InvoiceDay.el).empty();
                $(self.BookingDay.el).append('<span>' + result['booking'][0]['count'] + '</span>');
                $(self.DistanceDay.el).append('<span>' + (result['distance'][0]['sum'] || 0) + '</span>');
                $(self.AmountDay.el).append('<span>' + (result['amount'][0]['sum'] || 0) + '</span>');
                $(self.InvoiceDay.el).append('<span>' + (result['invoice'][0]['sum'] || 0)+ '</span>');
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        }

    onclick_this_year(ev) {//Function shows a year filtered dashboard
            self = this;
            jsonrpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
                model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
                kwargs:{}
            })
            .then(function (result) {
                $('#booking_this_day').hide();
                $('#distance_this_day').hide();
                $('#amount_this_day').hide();
                $('#invoice_this_day').hide();
                $('#booking_this_month').hide();
                $('#distance_this_month').hide();
                $('#amount_this_month').hide();
                $('#invoice_this_month').hide();
                $('#booking_this_week').hide();
                $('#distance_this_week').hide();
                $('#amount_this_week').hide();
                $('#invoice_this_week').hide();
                $('.total').hide();
                $('#booking_this_year').show();
                $('#distance_this_year').show();
                $('#amount_this_year').show();
                $('#invoice_this_year').show();
                $(self.BookingYear.el).empty();
                $(self.DistanceYear.el).empty();
                $(self.AmountYear.el).empty();
                $(self.InvoiceYear.el).empty();
                $(self.BookingYear.el).append('<span>' + result['booking'][0]['count'] + '</span>');
                $(self.DistanceYear.el).append('<span>' + (result['distance'][0]['sum'] || 0) + '</span>');
                $(self.AmountYear.el).append('<span>' + (result['amount'][0]['sum']  || 0) + '</span>');
                $(self.InvoiceYear.el).append('<span>' + (result['invoice'][0]['sum'] || 0) + '</span>');
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
            jsonrpc('/web/dataset/call_kw/truck.booking/get_select_filter',{
               model: 'truck.booking',
               method: 'get_select_filter',
               args: [ev],
               kwargs:{}
            })
            .then(function (result) {
                $('.total').hide();
                $('#booking_this_year').hide();
                $('#distance_this_year').hide();
                $('#amount_this_year').hide();
                $('#invoice_this_year').hide();
                $('#booking_this_day').hide();
                $('#distance_this_day').hide();
                $('#amount_this_day').hide();
                $('#invoice_this_day').hide();
                $('#booking_this_week').hide();
                $('#distance_this_week').hide();
                $('#amount_this_week').hide();
                $('#invoice_this_week').hide();
                $('#booking_this_month').show();
                $('#distance_this_month').show();
                $('#amount_this_month').show();
                $('#invoice_this_month').show();

                $(self.BookingMonth.el).empty();
                $(self.DistanceMonth.el).empty();
                $(self.AmountMonth.el).empty();
                $(self.InvoiceMonth.el).empty();

                $(self.BookingMonth.el).append('<span>' + result['booking'][0]['count'] + '</span>');
                $(self.DistanceMonth.el).append('<span>' + (result['distance'][0]['sum'] || 0) + '</span>');
                $(self.AmountMonth.el).append('<span>' + (result['amount'][0]['sum'] || 0) + '</span>');
                $(self.InvoiceMonth.el).append('<span>' + (result['invoice'][0]['sum'] || 0) + '</span>');

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
        new Chart($("#booking"), {
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
        new Chart($("#truck"), {
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
        new Chart($("#cust_distance"), {
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
        new Chart($("#truck_distance"), {
                        type: 'line',
                    data: {
                        labels: result.truck_distance_name,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.truck_distance_count, // Specify the data values array
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
                        responsive: true, // Instruct chart js to respond nicely.
                    }
                    });
    }

    get_cust_weight(result){//function to create a chart which shows the total goods weight according to the customer
        new Chart($("#cust_weight"), {
                        type: 'line',
                    data: {
                        labels: result.cust_weight_name,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.cust_weight_count, // Specify the data values array
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
                        responsive: true, // Instruct chart js to respond nicely.
                    }
                    });
    }

    get_truck_weight (result){//function to create a chart which shows the total goods weight according to the truck
    new Chart($("#truck_weight"), {
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
PackersManagement.template = "CustomDashBoard"
registry.category("actions").add("dash_tags", PackersManagement)
