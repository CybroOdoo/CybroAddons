/** @odoo-module **/
import { registry } from "@web/core/registry";
import { onWillStart, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
import { _t } from "@web/core/l10n/translation";
var op_type;
/* This class represents dashboard in Inventory. */
class CustomDashBoard extends owl.Component {
    setup() {
        this.orm = useService('orm')
        this.rootRef = useRef('root')
        // When the component is about to start, fetch data in tiles
        onWillStart(async () => {
            var self = this;
            this.props.title = 'Dashboard';
            var total_count = this.orm.call('venue.booking', 'get_total_booking')
                .then(function(result) {
                    self.props.booking_count = result.total_booking
                    self.props.total_venue = result.total_venue
                    self.props.total_amount = result.total_amount
                    self.props.total_invoice = result.total_invoice
                })
            var table_content = this.orm.call('venue.booking', 'get_top_venue')
                .then(function(result) {
                    self.props.upcoming = result.upcoming
                    self.props.venue = result.venue
                    self.props.customer = result.customer
                })
            return $.when(total_count, table_content)
        });
        // When the component is mounted, render various charts
        onMounted(async () => {
            this.render_booking();
            this.render_venue();
        });
    }
    //Function for render booking graph
    render_booking() {
        var self = this
        var ctx = $("#booking");
        this.orm.call('venue.booking', 'get_select_filter', [$("#stock_selection").val()])
            .then(function(result) {
                var data = {
                    labels: result.cust_invoice_name,
                    datasets: [{
                        label: 'Count',
                        data: result.cust_invoice_count,
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16"
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
                            "#6d5c16"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        fill: false
                    }, ]
                };
                var options = {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                };
                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: options
                });
            });
    }
    //Function for render venue graph
    render_venue() {
        var self = this
        var ctx = $("#venue");
        this.orm.call('venue.booking', 'get_select_filter', [$("#stock_selection").val()])
            .then(function(result) {
                var data = {
                    labels: result.truck_invoice_name,
                    datasets: [{
                        label: 'Count',
                        data: result.truck_invoice_sum,
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
                        fill: false
                    }, ]
                };

                var options = {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                };
                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "pie",
                    data: data,
                    options: options
                });
            });
    }
    //Function for filter the dashboard content
    on_change_booking_values(e) {
        e.stopPropagation();
        var $target = $(e.target);
        var value = $target.val();
        if (value == "year") {
            this.onclick_this_year($target.val());
        } else if (value == "quarter") {
            this.onclick_this_quarter($target.val());
        } else if (value == "month") {
            this.onclick_this_month($target.val());
        } else if (value == "week") {
            this.onclick_this_week($target.val());
        }
    }
    //Function for monthly filter on dashboard content
    onclick_this_month(ev) {
        self = this;
        this.orm.call('venue.booking', 'get_select_filter', [ev])
            .then(function(result) {
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
                $('#booking_this_month').empty();
                $('#amount_this_month').empty();
                $('#invoice_this_month').empty();
                $('#booking_this_month').append('<span>' + result['booking'][0]['count'] + '</span>');
                $('#distance_this_month').append('<span>' + result['venue_count'][0]['count'] + '</span>');
                if (result['amount'][0].sum) {
                    $('#amount_this_month').append('<span>' + result['amount'][0].sum + '</span>');
                } else {
                    $('#amount_this_month').append('<span>' + 0 + '</span>');
                }
                if (result['invoice'][0].sum) {
                    $('#invoice_this_month').append('<span>' + result['invoice'][0].sum + '</span>');
                } else {
                    $('#invoice_this_month').append('<span>' + 0 + '</span>')
                }
            })
    }
    //Function for yearly filter on dashboard content
    onclick_this_year(ev) {
        self = this;
        this.orm.call('venue.booking', 'get_select_filter', [ev])
            .then(function(result) {
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
                $('#booking_this_year').empty();
                $('#amount_this_year').empty();
                $('#invoice_this_year').empty();
                $('#venue_this_year').empty();
                $('#booking_this_year').append('<span>' + result['booking'][0]['count'] + '</span>');
                $('#venue_this_year').append('<span>' + result['venue_count'][0]['count'] + '</span>');
                if (result['amount'][0].sum) {
                    $('#amount_this_year').append('<span>' + result['amount'][0].sum + '</span>');
                } else {
                    $('#amount_this_year').append('<span>' + 0 + '</span>');
                }
                if (result['invoice'][0].sum) {
                    $('#invoice_this_year').append('<span>' + result['invoice'][0].sum + '</span>');
                } else {
                    $('#invoice_this_year').append('<span>' + 0 + '</span>')
                }
            })
    }
    //Function for daily filter on dashboard content
    onclick_this_day(ev) {
        self = this;
        this.orm.call('venue.booking', 'get_select_filter', [ev])
            .then(function(result) {
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
                $('#amount_this_day').show();
                $('#invoice_this_day').show();
                $('#booking_this_day').empty();
                $('#amount_this_day').empty();
                $('#invoice_this_day').empty();
                $('#venue_this_day').empty();
                $('#booking_this_day').append('<span>' + result['booking'][0]['count'] + '</span>');
                $('#venue_this_day').append('<span>' + result['venue_count'][0]['count'] + '</span>');
                if (result['amount'][0].sum) {
                    $('#amount_this_day').append('<span>' + result['amount'][0].sum + '</span>');
                } else {
                    $('#amount_this_day').append('<span>' + 0 + '</span>');
                }
                if (result['invoice'][0].sum) {
                    $('#invoice_this_day').append('<span>' + result['invoice'][0].sum + '</span>');
                } else {
                    $('#invoice_this_day').append('<span>' + 0 + '</span>')
                }
            })
    }
    //Function for weekly filter on dashboard content
    onclick_this_week(ev) {
        self = this;
        this.orm.call('venue.booking', 'get_select_filter', [ev])
            .then(function(result) {
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
                $('#amount_this_week').show();
                $('#invoice_this_week').show();
                $('#booking_this_week').empty();
                $('#amount_this_week').empty();
                $('#invoice_this_week').empty();
                $('#venue_this_week').empty();
                $('#booking_this_week').append('<span>' + result['booking'][0].count + '</span>');
                $('#venue_this_week').append('<span>' + result['venue_count'][0].count + '</span>');
                if (result['amount'][0].sum) {
                    $('#amount_this_week').append('<span>' + result['amount'][0].sum + '</span>');
                } else {
                    $('#amount_this_week').append('<span>' + 0 + '</span>');
                }
                if (result['invoice'][0].sum) {
                    $('#invoice_this_week').append('<span>' + result['invoice'][0].sum + '</span>');
                } else {
                    $('#invoice_this_week').append('<span>' + 0 + '</span>')
                }
            })
    }
}
CustomDashBoard.template = "CustomDashBoard";
actionRegistry.add('dashboard_tags', CustomDashBoard);
