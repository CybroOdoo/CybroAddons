/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { onMounted, useRef } from "@odoo/owl";
const actionRegistry = registry.category("actions");
    /** Create component 'CleaningDashboard' by extending Component **/
export class CleaningDashboard extends Component {
        /**
         *  Obtain yearly, monthly, quarterly, and weekly bookings,
         as well as clean and dirt reports.
         */
         setup() {
            super.setup(...arguments);
            this.orm = useService('orm');
            this.rootRef = useRef('main-content');
            this.today_sale = [];

            // When the component is mounted, render various charts
            onMounted(async () => {
                await this.RenderDashboard();
                await this.render_graph();
                const Ref = this.rootRef.el;

                // Hide and show elements using native JavaScript
                Ref.querySelector("#activity_week").style.display = 'none';
                Ref.querySelector("#activity_year").style.display = 'none';
                Ref.querySelector("#activity_quarter").style.display = 'none';
                Ref.querySelector("#activity_month").style.display = 'block';

                Ref.querySelector("#quality_week").style.display = 'none';
                Ref.querySelector("#quality_month").style.display = 'block';
                Ref.querySelector("#quality_quarter").style.display = 'none';
                Ref.querySelector("#quality_year").style.display = 'none';

                // ORM call
                await this.orm.call('cleaning.management.dashboard', 'cleaning_count', [0]).then(function(result) {
                    const report = Ref.querySelector(".report");
                    const bookings = Ref.querySelector(".bookings");
                    const quality = Ref.querySelector(".quality");

                    if (result['inspections'].length > 0 && result['bookings'].length > 0) {
                        report.style.display = 'block';
                        bookings.style.display = 'block';
                        quality.style.display = 'block';
                    } else if (result['bookings'].length > 0) {
                        report.style.display = 'block';
                        bookings.style.display = 'block';
                        quality.style.display = 'none';
                    } else if (result['inspections'].length > 0) {
                        report.style.display = 'block';
                        bookings.style.display = 'block';
                        quality.style.display = 'block';
                    } else {
                        report.style.display = 'none';
                        bookings.style.display = 'none';
                        quality.style.display = 'none';
                    }
                });
            });
        }
        ChangeFiltration(ev) {
            console.log("ChangeFiltration", ev)
            ev.stopPropagation();
            // Return elements where event occurred
            var option_val = ev.target.value;
            if (option_val == "this_year") {
                this.OnclickThisYear(option_val);
            } else if (option_val == "this_quarter") {
                this.OnclickThisQuarter(option_val);
            } else if (option_val == "this_month") {
                this.OnclickThisMonth(option_val);
            } else if (option_val == "this_week") {
                this.OnclickThisWeek(option_val);
            }
        }
        //Generate a dashboard displaying the count of bookings, dirty instances, completed cleanings, and the cleaning team.
        RenderDashboard() {
                console.log("RenderDashboard")
            var self = this;
            this.orm.call('cleaning.management.dashboard',
            'get_dashboard_count', [0]).then(function(result) {
                const MainDiv = self.rootRef.el
                const bookings_count = MainDiv.querySelector("#bookings_count")
                bookings_count.classList.add("stat-digit");
                bookings_count.textContent = result.bookings;
                const teams_count = MainDiv.querySelector("#teams_count")
                teams_count.classList.add("stat-digit");
                teams_count.textContent = result.teams;
                const cleaning_count = MainDiv.querySelector("#cleaning_count")
                cleaning_count.classList.add("stat-digit");
                cleaning_count.textContent = result.cleaned;
                const dirty_count = MainDiv.querySelector("#dirty_count")
                dirty_count.classList.add("stat-digit");
                dirty_count.textContent = result.dirty;
                });
        }
        //Get booking records
        GetBookings() {
            console.log("GetBookings", )
            this.env.services.action.doAction({
                name: ("Bookings"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.booking',
                view_mode: 'list,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['state', '=', 'booked']
                ],
                target: 'current',
            })
        }
        //Get team count records
        GetTeams() {
            this.env.services.action.doAction({
                name: ("Teams"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.team',
                view_mode: 'list,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
            })
        }
        //Get cleaning count
        GetCleaning() {
            this.env.services.action.doAction({
                name: ("Count of Cleaning"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.inspection',
                view_mode: 'list,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['state', '=', 'cleaned']
                ],
                target: 'current',
            })
        }
        //Get dirty count
        GetDirty() {
            this.env.services.action.doAction({
                name: ("Count of dirty"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.inspection',
                view_mode: 'list,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'dirty']],
                target: 'current',
            })
        }
        //Generate a graph representing the yearly, monthly, weekly, and quarterly records.
        render_graph() {
            console.log("render_graph")
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_bookings_year")
            console.log("ctx", ctx)
            this.orm.call('cleaning.management.dashboard', 'get_the_booking_year', [0])
            .then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_year'],
                    self.total_booking_stage_draft_year =
                    result['total_booking_stage_draft_year'],
                    self.total_booking_stage_booked_year =
                    result['total_booking_stage_booked_year'],
                    self.total_booking_stage_cleaned_year =
                    result['total_booking_stage_cleaned_year'],
                    self.total_booking_stage_canceled_year =
                    result['total_booking_stage_canceled_year']
                var ctx = self.rootRef.el.querySelector("#activity_year")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_year'],
                        datasets: [{
                            label: 'Stage', data: [
                                result['total_booking_stage_draft_year'],
                                result['total_booking_stage_booked_year'],
                                result['total_booking_stage_cleaned_year'],
                                result['total_booking_stage_canceled_year']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_bookings_week")
            this.orm.call('cleaning.management.dashboard', 'get_the_booking_week', [0]).then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_week'],
                    self.total_booking_stage_draft =
                    result['total_booking_stage_draft_week'],
                    self.total_booking_stage_booked =
                    result['total_booking_stage_booked_week'],
                    self.total_booking_stage_cleaned =
                    result['total_booking_stage_cleaned_week'],
                    self.total_booking_stage_canceled =
                    result['total_booking_stage_canceled_week']
                var ctx = self.rootRef.el.querySelector("#activity_week")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_week'],
                        datasets: [{
                            label: 'Stage',
                            data: [
                    result['total_booking_stage_draft_week'],
                    result['total_booking_stage_booked_week'],
                    result['total_booking_stage_cleaned_week'],
                    result['total_booking_stage_canceled_week']
                ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_bookings_month")
            this.orm.call('cleaning.management.dashboard', 'get_the_booking_month', [0]).then(function(result) {
                const dataPoints = [
                    result['total_booking_stage_draft_month'],
                    result['total_booking_stage_booked_month'],
                    result['total_booking_stage_cleaned_month'],
                    result['total_booking_stage_canceled_month']
                ].filter(value => value !== null && value !== '' &&
                    value !== 0);
                var ctx = self.rootRef.el.querySelector("#activity_month")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_month'],
                        datasets: [{
                            label: 'Stage',
                            data: dataPoints,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_bookings_quarter")
            this.orm.call('cleaning.management.dashboard', 'get_the_booking_quarter', [0]).then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_quarter'],
                    self.total_booking_stage_draft =
                    result['total_booking_stage_draft_quarter'],
                    self.total_booking_stage_booked =
                    result['total_booking_stage_booked_quarter'],
                    self.total_booking_stage_cleaned =
                    result['total_booking_stage_cleaned_quarter'],
                    self.total_booking_stage_canceled =
                    result['total_booking_stage_canceled_quarter']
                const ctx = self.rootRef.el.querySelector("#activity_quarter")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_quarter'],
                        datasets: [{
                            label: 'Stage',
                            data: [
                    result['total_booking_stage_draft_quarter'],
                    result['total_booking_stage_booked_quarter'],
                    result['total_booking_stage_cleaned_quarter'],
                    result['total_booking_stage_canceled_quarter']
                ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_quality_year")
            this.orm.call('cleaning.management.dashboard', 'quality_year', [0]).then(function(result) {
                self.quality_year = result['quality_year'],
                self.cleaned_quality_year = result['cleaned_quality_year'],
                self.dirty_quality_year = result['dirty_quality_year']
                const ctx = self.rootRef.el.querySelector("#quality_year")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_year'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_year'],
                                result['dirty_quality_year']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_quality_week")
            this.orm.call('cleaning.management.dashboard', 'quality_week', [0]).then(function(result) {
                self.quality_week = result['quality_week'],
                self.cleaned_quality_week = result['cleaned_quality_week'],
                self.dirty_quality_week = result['dirty_quality_week']
                const ctx = self.rootRef.el.querySelector("#quality_week")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_week'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_week'],
                                result['dirty_quality_week']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_quality_month")
            this.orm.call('cleaning.management.dashboard', 'quality_month', [0]).then(function(result) {
                self.quality_month = result['quality_month'],
                self.cleaned_quality_month = result['cleaned_quality_month'],
                self.dirty_quality_month = result['dirty_quality_month']
                const ctx = self.rootRef.el.querySelector("#quality_month")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_month'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_month'],
                                result['dirty_quality_month']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.rootRef.el.querySelector(".total_quality_quarter")
            this.orm.call('cleaning.management.dashboard', 'quality_quarter', [0]).then(function(result) {
                self.quality_quarter = result['quality_quarter'];
                self.cleaned_quality_year = result['cleaned_quality_quarter'];
                self.dirty_quality_year = result['dirty_quality_quarter'];
                const ctx = self.rootRef.el.querySelector("#quality_quarter")
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_quarter'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_quarter'],
                                result['dirty_quality_quarter']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                })
            })
        }
        //  Show yearly result
        OnclickThisYear(ev) {
            console.log("OnclickThisYear");
            const Ref = this.rootRef.el;  // Assuming you already have a reference to the root element

            Ref.querySelector("#activity_week").style.display = 'none';
            Ref.querySelector("#activity_month").style.display = 'none';
            Ref.querySelector("#activity_quarter").style.display = 'none';
            Ref.querySelector("#activity_year").style.display = 'block';

            Ref.querySelector("#quality_week").style.display = 'none';
            Ref.querySelector("#quality_month").style.display = 'none';
            Ref.querySelector("#quality_quarter").style.display = 'none';
            Ref.querySelector("#quality_year").style.display = 'block';
        }
        //    Show monthly result
        OnclickThisMonth(ev) {
            const Ref = this.rootRef.el;  // Assuming you already have a reference to the root element
            Ref.querySelector("#activity_week").style.display = 'none';
            Ref.querySelector("#activity_year").style.display = 'none';
            Ref.querySelector("#activity_quarter").style.display = 'none';
            Ref.querySelector("#activity_month").style.display = 'block';

            Ref.querySelector("#quality_week").style.display = 'none';
            Ref.querySelector("#quality_month").style.display = 'block';
            Ref.querySelector("#quality_quarter").style.display = 'none';
            Ref.querySelector("#quality_year").style.display = 'none';
        }
        //    Show weekly result
        OnclickThisWeek(ev) {
            const Ref = this.rootRef.el;  // Assuming you already have a reference to the root element
            Ref.querySelector("#activity_year").style.display = 'none';
            Ref.querySelector("#activity_month").style.display = 'none';
            Ref.querySelector("#activity_quarter").style.display = 'none';
            Ref.querySelector("#activity_week").style.display = 'block';

            Ref.querySelector("#quality_week").style.display = 'block';
            Ref.querySelector("#quality_month").style.display = 'none';
            Ref.querySelector("#quality_quarter").style.display = 'none';
            Ref.querySelector("#quality_year").style.display = 'none';

        }
        //    Show quarterly result
        OnclickThisQuarter(ev) {
            const Ref = this.rootRef.el;  // Assuming you already have a reference to the root element
            Ref.querySelector("#activity_week").style.display = 'none';
            Ref.querySelector("#activity_month").style.display = 'none';
            Ref.querySelector("#activity_year").style.display = 'none';
            Ref.querySelector("#activity_quarter").style.display = 'block';

            Ref.querySelector("#quality_week").style.display = 'none';
            Ref.querySelector("#quality_month").style.display = 'none';
            Ref.querySelector("#quality_quarter").style.display = 'block';
            Ref.querySelector("#quality_year").style.display = 'none';

        }
}
CleaningDashboard.template = "CleaningDashBoard";
actionRegistry.add("cleaning_dashboard_tags", CleaningDashboard);
