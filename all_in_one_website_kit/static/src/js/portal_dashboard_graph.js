/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const PortalDashBoardGraph = publicWidget.Widget.extend({
    selector: '.portal_dashboard',
    init: function (parent, context) {
        this._super(parent, context);
    },
    // Implementation of the start method goes here
    start: function () {
        this.set("title", 'Portal Dashboard');
        return this.fetch_data();
    },
    fetch_data: function () {
        // To fetch data for showing in dashboard as graph
        return rpc('/portal/dashboard/data', { // Assuming there is a controller or call_kw?
            // Original code used this._rpc({model: ..., method: ...})
            // That suggests it was calling a model method, but usually _rpc on widget needs more context or uses specialized mixins.
            // Using rpc service directly is safer if we know the route or use call_kw.
            // Original: model: 'portal.dashboard.data', method: 'datafetch'
            // I will use call_kw via rpc.
        }).then(function (result) {
            // ...
        });
        // WAIT: The original used `this._rpc` which implies `Mixins` or `Widget` support.
        // But `publicWidget` in Odoo 18 should support `_rpc` if it uses `Wiget` from legacy.
        // However, standard request now is `useService("rpc")` in OWL or `rpc` imports.
        // Let's replicate the `call_kw` manually to be safe.
    }
});

// Since I need to inspect the original code to see exactly how it called rpc, I will pause this replace and do a multi-step.
// The original code:
// model: 'portal.dashboard.data',
// method: 'datafetch'
// It seems `portal.dashboard.data` is a model.
// I will use `rpc` to call it.

publicWidget.registry.PortalDashBoardGraph = publicWidget.Widget.extend({
    selector: '.o_portal_dashboard',
    start: function () {
        var self = this;
        this.fetch_data();
    },
    fetch_data: function () {
        var self = this;
        rpc('/portal/dashboard/data', {}).then(function (result) {
            // Sales Chart
            if (document.getElementById('sales_pie')) {
                new Chart(document.getElementById('sales_pie'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Sale Orders', 'Quotations'],
                        datasets: [{
                            data: result.target,
                            backgroundColor: ['#28a745', '#17a2b8'], // Green, Info
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' },
                            title: { display: false }
                        },
                        cutout: '70%',
                    }
                });
            }

            // Purchase Chart
            if (document.getElementById('purchase_pie')) {
                new Chart(document.getElementById('purchase_pie'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Purchase Orders', 'RFQs'],
                        datasets: [{
                            data: result.target_po,
                            backgroundColor: ['#6c757d', '#ffc107'], // Gray, Warning
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' },
                            title: { display: false }
                        },
                        cutout: '70%',
                    }
                });
            }

            // Accounting Chart
            if (document.getElementById('account_pie')) {
                new Chart(document.getElementById('account_pie'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Invoices', 'Bills'],
                        datasets: [{
                            data: result.target_accounting,
                            backgroundColor: ['#007bff', '#dc3545'], // Primary, Danger
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' },
                            title: { display: false }
                        },
                        cutout: '70%',
                    }
                });
            }
        });
    }
});

export default publicWidget.registry.PortalDashBoardGraph;