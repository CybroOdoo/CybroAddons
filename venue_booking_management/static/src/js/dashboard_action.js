/** @odoo-module **/

import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const actionRegistry = registry.category("actions");

/* This class represents dashboard in Inventory. */
class CustomDashBoard extends Component {
    static template = "CustomDashBoard";

    setup() {
        this.orm = useService('orm');
        this.bookingCanvasRef = useRef('booking'); // Ref for booking chart canvas
        this.venueCanvasRef = useRef('venue'); // Ref for venue chart canvas
        this.stockSelectionRef = useRef('stock_selection'); // Ref for stock selection input

        // Refs for dashboard metrics
        this.totalBookingRef = useRef('total_booking'); // Updated ref for total booking
        this.totalVenueRef = useRef('total_venue'); // Updated ref for total venue
        this.totalAmountRef = useRef('total_amount'); // Updated ref for total amount
        this.totalInvoiceRef = useRef('total_invoice'); // Updated ref for total invoice
        this.bookingThisYearRef = useRef('booking_this_year');
        this.venueThisYearRef = useRef('venue_this_year');
        this.amountThisYearRef = useRef('amount_this_year');
        this.invoiceThisYearRef = useRef('invoice_this_year');
        this.bookingThisDayRef = useRef('booking_this_day');
        this.venueThisDayRef = useRef('venue_this_day');
        this.amountThisDayRef = useRef('amount_this_day');
        this.invoiceThisDayRef = useRef('invoice_this_day');
        this.bookingThisWeekRef = useRef('booking_this_week');
        this.venueThisWeekRef = useRef('venue_this_week');
        this.amountThisWeekRef = useRef('amount_this_week');
        this.invoiceThisWeekRef = useRef('invoice_this_week');
        this.bookingThisMonthRef = useRef('booking_this_month');
        this.venueThisMonthRef = useRef('venue_this_month');
        this.amountThisMonthRef = useRef('amount_this_month');
        this.invoiceThisMonthRef = useRef('invoice_this_month');

        // When the component is about to start, fetch data for tiles
        onWillStart(async () => {
            const totalCount = this.orm.call('venue.booking', 'get_total_booking').then(result => {
                this.props.booking_count = result.total_booking;
                this.props.total_venue = result.total_venue;
                this.props.total_amount = result.total_amount;
                this.props.total_invoice = result.total_invoice;
            });

            const tableContent = this.orm.call('venue.booking', 'get_top_venue').then(result => {
                this.props.upcoming = result.upcoming;
                this.props.venue = result.venue;
                this.props.customer = result.customer;
            });

            await Promise.all([totalCount, tableContent]);
        });

        // When the component is mounted, render charts
        onMounted(() => {
            this.render_booking();
            this.render_venue();
        });
    }

    // Function to render booking chart
    render_booking() {
        const ctx = this.bookingCanvasRef.el; // Use OWL's useRef to get canvas element
        this.orm.call('venue.booking', 'get_select_filter', [this.stockSelectionRef.el.value]).then(result => {
            const data = {
                labels: result.cust_invoice_name,
                datasets: [{
                    label: _t('Count'),
                    data: result.cust_invoice_count,
                    backgroundColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191",
                        "#d45087", "#ff7c43", "#ffa600", "#a05195", "#6d5c16"
                    ],
                    borderColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191",
                        "#d45087", "#ff7c43", "#ffa600", "#a05195", "#6d5c16"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    fill: false
                }]
            };

            const options = {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            };

            // Create Chart.js object
            new Chart(ctx, {
                type: "bar",
                data: data,
                options: options
            });
        });
    }

    // Function to render venue chart
    render_venue() {
        const ctx = this.venueCanvasRef.el; // Use OWL's useRef to get canvas element
        this.orm.call('venue.booking', 'get_select_filter', [this.stockSelectionRef.el.value]).then(result => {
            const data = {
                labels: result.truck_invoice_name,
                datasets: [{
                    label: _t('Count'),
                    data: result.truck_invoice_sum,
                    backgroundColor: [
                        "#665191", "#ff7c43", "#ffa600", "#d45087",
                        "#a05195", "#6d5c16", "#CCCCFF", "#003f5c",
                        "#2f4b7c", "#f95d6a"
                    ],
                    borderColor: [
                        "#003f5c", "#2f4b7c", "#f95d6a", "#665191",
                        "#d45087", "#ff7c43", "#ffa600", "#a05195",
                        "#6d5c16", "#CCCCFF"
                    ],
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1,
                    fill: false
                }]
            };

            const options = {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            };

            // Create Chart.js object
            new Chart(ctx, {
                type: "pie",
                data: data,
                options: options
            });
        });
    }

    // Function to filter dashboard content
    on_change_booking_values(e) {
        e.stopPropagation();
        const value = this.stockSelectionRef.el.value; // Use OWL ref to get value
        if (value === "year") {
            this.onclick_this_year(value);
        } else if (value === "quarter") {
            this.onclick_this_quarter(value);
        } else if (value === "month") {
            this.onclick_this_month(value);
        } else if (value === "week") {
            this.onclick_this_week(value);
        } else if (value === "day") {
            this.onclick_this_day(value);
        }
    }

    // Function for monthly filter on dashboard content
    onclick_this_month(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            this.totalBookingRef.el.style.display = 'none';
            this.totalVenueRef.el.style.display = 'none';
            this.totalAmountRef.el.style.display = 'none';
            this.totalInvoiceRef.el.style.display = 'none';
            this.bookingThisYearRef.el.style.display = 'none';
            this.venueThisYearRef.el.style.display = 'none';
            this.amountThisYearRef.el.style.display = 'none';
            this.invoiceThisYearRef.el.style.display = 'none';
            this.bookingThisDayRef.el.style.display = 'none';
            this.venueThisDayRef.el.style.display = 'none';
            this.amountThisDayRef.el.style.display = 'none';
            this.invoiceThisDayRef.el.style.display = 'none';
            this.bookingThisWeekRef.el.style.display = 'none';
            this.venueThisWeekRef.el.style.display = 'none';
            this.amountThisWeekRef.el.style.display = 'none';
            this.invoiceThisWeekRef.el.style.display = 'none';

            // Show monthly sections
            this.bookingThisMonthRef.el.style.display = 'block';
            this.venueThisMonthRef.el.style.display = 'block';
            this.amountThisMonthRef.el.style.display = 'block';
            this.invoiceThisMonthRef.el.style.display = 'block';

            // Update content
            this.bookingThisMonthRef.el.innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            this.venueThisMonthRef.el.innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            this.amountThisMonthRef.el.innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            this.invoiceThisMonthRef.el.innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for yearly filter on dashboard content
    onclick_this_year(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            this.totalBookingRef.el.style.display = 'none';
            this.totalVenueRef.el.style.display = 'none';
            this.totalAmountRef.el.style.display = 'none';
            this.totalInvoiceRef.el.style.display = 'none';
            this.bookingThisDayRef.el.style.display = 'none';
            this.venueThisDayRef.el.style.display = 'none';
            this.amountThisDayRef.el.style.display = 'none';
            this.invoiceThisDayRef.el.style.display = 'none';
            this.bookingThisMonthRef.el.style.display = 'none';
            this.venueThisMonthRef.el.style.display = 'none';
            this.amountThisMonthRef.el.style.display = 'none';
            this.invoiceThisMonthRef.el.style.display = 'none';
            this.bookingThisWeekRef.el.style.display = 'none';
            this.venueThisWeekRef.el.style.display = 'none';
            this.amountThisWeekRef.el.style.display = 'none';
            this.invoiceThisWeekRef.el.style.display = 'none';

            // Show yearly sections
            this.bookingThisYearRef.el.style.display = 'block';
            this.venueThisYearRef.el.style.display = 'block';
            this.amountThisYearRef.el.style.display = 'block';
            this.invoiceThisYearRef.el.style.display = 'block';

            // Update content
            this.bookingThisYearRef.el.innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            this.venueThisYearRef.el.innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            this.amountThisYearRef.el.innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            this.invoiceThisYearRef.el.innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for daily filter on dashboard content
    onclick_this_day(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            this.totalBookingRef.el.style.display = 'none';
            this.totalVenueRef.el.style.display = 'none';
            this.totalAmountRef.el.style.display = 'none';
            this.totalInvoiceRef.el.style.display = 'none';
            this.bookingThisMonthRef.el.style.display = 'none';
            this.venueThisMonthRef.el.style.display = 'none';
            this.amountThisMonthRef.el.style.display = 'none';
            this.invoiceThisMonthRef.el.style.display = 'none';
            this.bookingThisWeekRef.el.style.display = 'none';
            this.venueThisWeekRef.el.style.display = 'none';
            this.amountThisWeekRef.el.style.display = 'none';
            this.invoiceThisWeekRef.el.style.display = 'none';
            this.bookingThisYearRef.el.style.display = 'none';
            this.venueThisYearRef.el.style.display = 'none';
            this.amountThisYearRef.el.style.display = 'none';
            this.invoiceThisYearRef.el.style.display = 'none';

            // Show daily sections
            this.bookingThisDayRef.el.style.display = 'block';
            this.venueThisDayRef.el.style.display = 'block';
            this.amountThisDayRef.el.style.display = 'block';
            this.invoiceThisDayRef.el.style.display = 'block';

            // Update content
            this.bookingThisDayRef.el.innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            this.venueThisDayRef.el.innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            this.amountThisDayRef.el.innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            this.invoiceThisDayRef.el.innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for weekly filter on dashboard content
    onclick_this_week(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            this.totalBookingRef.el.style.display = 'none';
            this.totalVenueRef.el.style.display = 'none';
            this.totalAmountRef.el.style.display = 'none';
            this.totalInvoiceRef.el.style.display = 'none';
            this.bookingThisMonthRef.el.style.display = 'none';
            this.venueThisMonthRef.el.style.display = 'none';
            this.amountThisMonthRef.el.style.display = 'none';
            this.invoiceThisMonthRef.el.style.display = 'none';
            this.bookingThisYearRef.el.style.display = 'none';
            this.venueThisYearRef.el.style.display = 'none';
            this.amountThisYearRef.el.style.display = 'none';
            this.invoiceThisYearRef.el.style.display = 'none';
            this.bookingThisDayRef.el.style.display = 'none';
            this.venueThisDayRef.el.style.display = 'none';
            this.amountThisDayRef.el.style.display = 'none';
            this.invoiceThisDayRef.el.style.display = 'none';

            // Show weekly sections
            this.bookingThisWeekRef.el.style.display = 'block';
            this.venueThisWeekRef.el.style.display = 'block';
            this.amountThisWeekRef.el.style.display = 'block';
            this.invoiceThisWeekRef.el.style.display = 'block';

            // Update content
            this.bookingThisWeekRef.el.innerHTML = `<span>${result['booking'][0].count}</span>`;
            this.venueThisWeekRef.el.innerHTML = `<span>${result['venue_count'][0].count}</span>`;
            this.amountThisWeekRef.el.innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            this.invoiceThisWeekRef.el.innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Placeholder for quarter filter (not implemented in original code)
    onclick_this_quarter(value) {
        // Implement quarter filter logic here if needed
        console.log(`Quarter filter not implemented for value: ${value}`);
    }
}

actionRegistry.add('dashboard_tags', CustomDashBoard);