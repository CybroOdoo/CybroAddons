odoo.define('all_in_one_website_kit.PortalDashBoardGraph', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var publicWidget = require('web.public.widget');
      /** Extends the public widget class to add the events
    */
    publicWidget.registry.PortalDashBoardGraph = publicWidget.Widget.extend({
        selector: '.portal_dashboard',
        init: function(parent, context) {
            this._super(parent, context);
        },
          // Implementation of the start method goes here
        start: function() {
            this.set("title", 'Portal Dashboard');
            this.fetch_data()
        },
        fetch_data: function() {
            // To fetch data for showing in dashboard as graph
            var def = this._rpc({
                model: 'portal.dashboard.data',
                method: 'datafetch'
            }).then(function(result) {
                // To set graph for sales
                const DATA_COUNT_so = ['Sale order', 'Quotations'];
                const NUMBER_CFG_so = {
                    count: DATA_COUNT_so,
                    min: 0,
                    max: 100
                };
                const labels_1 = ['Sale order', 'Quotations'];
                const data_1 = {
                    labels: labels_1,
                    datasets: [{
                        label: 'New',
                        data: result['target'],
                        backgroundColor: ['rgb(47, 79, 79)', 'rgb(15, 127, 127)'],
                    }]
                };
                const config_1 = {
                    type: 'pie',
                    data: data_1,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Sales Analysis'
                            }
                        }
                    },
                };
                // To set graph for purchase
                const DATA_COUNT_po = ['Purchase order', 'RFQ'];
                const NUMBER_CFG_po = {
                    count: DATA_COUNT_po,
                    min: 0,
                    max: 100
                };
                const labels_2 = ['Purchase order', 'RFQ'];
                const data_2 = {
                    labels: labels_2,
                    datasets: [{
                        label: 'New',
                        data: result['target_po'],
                        backgroundColor: ['rgb(107, 99, 99)', 'rgb(135, 147, 147)'],
                    }]
                };
                const config_2 = {
                    type: 'pie',
                    data: data_2,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Purchase Analysis'
                            }
                        }
                    },
                };
                // To set graph for account moves
                const DATA_COUNT_invoice = ['Invoices', 'Bill'];
                const NUMBER_CFG_invoice = {
                    count: DATA_COUNT_invoice,
                    min: 0,
                    max: 100
                };
                const labels_3 = ['Invoices', 'Bill'];
                const data_3 = {
                    labels: labels_3,
                    datasets: [{
                        label: 'New',
                        data: result['target_accounting'],
                        backgroundColor: ['rgb(207, 99, 99)', 'rgb(235, 187, 147)'],
                    }]
                };
                const config_3 = {
                    type: 'pie',
                    data: data_3,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Accounting Analysis'
                            }
                        }
                    },
                };
                const sales_pie = new Chart(document.getElementById('sales_pie'), config_1);
                const purchase_pie = new Chart(document.getElementById('purchase_pie'), config_2);
                const account_pie = new Chart(document.getElementById('account_pie'), config_3);
            });
            return $.when(def);
        },
    });
})