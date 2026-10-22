/** @odoo-module **/

import { Component, onWillStart, onMounted, signal, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const actionRegistry = registry.category("actions");

function getEl(ref) {
    if (!ref) return null;
    return ref.el || (typeof ref === "function" ? ref() : null);
}

/* This class represents dashboard in Inventory. */
class CustomDashBoard extends Component {
    static template = "CustomDashBoard";

    setup() {
        this.orm = useService('orm');

        // Internal reactive state using Owl 3 proxy
        this.state = proxy({
            booking_count: 0,
            total_venue: 0,
            total_amount: 0,
            total_invoice: 0,
            upcoming: [],
            customer: [],
            venue: [],
        });

        // Refs matching t-ref in QWeb template
        this.booking = signal.ref();
        this.venue = signal.ref();
        this.stock_selection = signal.ref();

        this.total_booking = signal.ref();
        this.total_venue = signal.ref();
        this.total_amount = signal.ref();
        this.total_invoice = signal.ref();

        this.booking_this_year = signal.ref();
        this.venue_this_year = signal.ref();
        this.amount_this_year = signal.ref();
        this.invoice_this_year = signal.ref();

        this.booking_this_day = signal.ref();
        this.venue_this_day = signal.ref();
        this.amount_this_day = signal.ref();
        this.invoice_this_day = signal.ref();

        this.booking_this_week = signal.ref();
        this.venue_this_week = signal.ref();
        this.amount_this_week = signal.ref();
        this.invoice_this_week = signal.ref();

        this.booking_this_month = signal.ref();
        this.venue_this_month = signal.ref();
        this.amount_this_month = signal.ref();
        this.invoice_this_month = signal.ref();

        // When the component is about to start, fetch data for tiles
        onWillStart(async () => {
            const totalCount = this.orm.call('venue.booking', 'get_total_booking').then(result => {
                this.state.booking_count = result.total_booking;
                this.state.total_venue = result.total_venue;
                this.state.total_amount = result.total_amount;
                this.state.total_invoice = result.total_invoice;
            });

            const tableContent = this.orm.call('venue.booking', 'get_top_venue').then(result => {
                this.state.upcoming = result.upcoming;
                this.state.venue = result.venue;
                this.state.customer = result.customer;
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
        const ctx = getEl(this.booking);
        const selectEl = getEl(this.stock_selection);
        this.orm.call('venue.booking', 'get_select_filter', [selectEl ? selectEl.value : 'month']).then(result => {
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

            if (ctx) {
                new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: options
                });
            }
        });
    }

    // Function to render venue chart
    render_venue() {
        const ctx = getEl(this.venue);
        const selectEl = getEl(this.stock_selection);
        this.orm.call('venue.booking', 'get_select_filter', [selectEl ? selectEl.value : 'month']).then(result => {
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

            if (ctx) {
                new Chart(ctx, {
                    type: "pie",
                    data: data,
                    options: options
                });
            }
        });
    }

    // Function to filter dashboard content
    on_change_booking_values(e) {
        e.stopPropagation();
        const selectEl = getEl(this.stock_selection);
        const value = selectEl ? selectEl.value : 'month';
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
            [this.total_booking, this.total_venue, this.total_amount, this.total_invoice,
            this.booking_this_year, this.venue_this_year, this.amount_this_year, this.invoice_this_year,
            this.booking_this_day, this.venue_this_day, this.amount_this_day, this.invoice_this_day,
            this.booking_this_week, this.venue_this_week, this.amount_this_week, this.invoice_this_week]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'none'; });

            // Show monthly sections
            [this.booking_this_month, this.venue_this_month, this.amount_this_month, this.invoice_this_month]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'block'; });

            // Update content
            if (getEl(this.booking_this_month)) getEl(this.booking_this_month).innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            if (getEl(this.venue_this_month)) getEl(this.venue_this_month).innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            if (getEl(this.amount_this_month)) getEl(this.amount_this_month).innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            if (getEl(this.invoice_this_month)) getEl(this.invoice_this_month).innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for yearly filter on dashboard content
    onclick_this_year(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            [this.total_booking, this.total_venue, this.total_amount, this.total_invoice,
            this.booking_this_day, this.venue_this_day, this.amount_this_day, this.invoice_this_day,
            this.booking_this_month, this.venue_this_month, this.amount_this_month, this.invoice_this_month,
            this.booking_this_week, this.venue_this_week, this.amount_this_week, this.invoice_this_week]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'none'; });

            // Show yearly sections
            [this.booking_this_year, this.venue_this_year, this.amount_this_year, this.invoice_this_year]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'block'; });

            // Update content
            if (getEl(this.booking_this_year)) getEl(this.booking_this_year).innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            if (getEl(this.venue_this_year)) getEl(this.venue_this_year).innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            if (getEl(this.amount_this_year)) getEl(this.amount_this_year).innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            if (getEl(this.invoice_this_year)) getEl(this.invoice_this_year).innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for daily filter on dashboard content
    onclick_this_day(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            [this.total_booking, this.total_venue, this.total_amount, this.total_invoice,
            this.booking_this_month, this.venue_this_month, this.amount_this_month, this.invoice_this_month,
            this.booking_this_week, this.venue_this_week, this.amount_this_week, this.invoice_this_week,
            this.booking_this_year, this.venue_this_year, this.amount_this_year, this.invoice_this_year]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'none'; });

            // Show daily sections
            [this.booking_this_day, this.venue_this_day, this.amount_this_day, this.invoice_this_day]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'block'; });

            // Update content
            if (getEl(this.booking_this_day)) getEl(this.booking_this_day).innerHTML = `<span>${result['booking'][0]['count']}</span>`;
            if (getEl(this.venue_this_day)) getEl(this.venue_this_day).innerHTML = `<span>${result['venue_count'][0]['count']}</span>`;
            if (getEl(this.amount_this_day)) getEl(this.amount_this_day).innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            if (getEl(this.invoice_this_day)) getEl(this.invoice_this_day).innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Function for weekly filter on dashboard content
    onclick_this_week(value) {
        this.orm.call('venue.booking', 'get_select_filter', [value]).then(result => {
            // Hide all sections
            [this.total_booking, this.total_venue, this.total_amount, this.total_invoice,
            this.booking_this_month, this.venue_this_month, this.amount_this_month, this.invoice_this_month,
            this.booking_this_year, this.venue_this_year, this.amount_this_year, this.invoice_this_year,
            this.booking_this_day, this.venue_this_day, this.amount_this_day, this.invoice_this_day]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'none'; });

            // Show weekly sections
            [this.booking_this_week, this.venue_this_week, this.amount_this_week, this.invoice_this_week]
                .forEach(r => { const el = getEl(r); if (el) el.style.display = 'block'; });

            // Update content
            if (getEl(this.booking_this_week)) getEl(this.booking_this_week).innerHTML = `<span>${result['booking'][0].count}</span>`;
            if (getEl(this.venue_this_week)) getEl(this.venue_this_week).innerHTML = `<span>${result['venue_count'][0].count}</span>`;
            if (getEl(this.amount_this_week)) getEl(this.amount_this_week).innerHTML = `<span>${result['amount'][0].sum || 0}</span>`;
            if (getEl(this.invoice_this_week)) getEl(this.invoice_this_week).innerHTML = `<span>${result['invoice'][0].sum || 0}</span>`;
        });
    }

    // Placeholder for quarter filter (not implemented in original code)
    onclick_this_quarter(value) {
        // Implement quarter filter logic here if needed
    }
}

actionRegistry.add('venue_booking_dashboard_tags', CustomDashBoard);
if (!actionRegistry.contains('dashboard_tags')) {
    actionRegistry.add('dashboard_tags', CustomDashBoard);
}