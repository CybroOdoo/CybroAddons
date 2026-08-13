/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.PortalDashBoardGraph = publicWidget.Widget.extend({
    selector: '.portal_dashboard',

    init: function (parent, context) {
        this._super(parent, context);
    },

    start: function () {
        this.fetch_data();
    },

    fetch_data: async function () {
            var result = await rpc('/web/dataset/call_kw', {
                model: 'portal.dashboard.data',
                method: 'datafetch',
                args: [],
                kwargs: {}
            });

            // For Sales Analysis
            const labels_1 = ['Sale order', 'Quotations'];
            const data_1 = {
                labels: labels_1,
                datasets: [
                    {
                        label: 'New',
                        data: result['target'],
                        backgroundColor: ['rgb(47, 79, 79)', 'rgb(15, 127, 127)'],
                    }
                ]
            };
            const config_1 = {
                type: 'pie',
                data: data_1,
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: 'Sales Analysis' }
                    }
                }
            };

            // For Purchase Analysis
            const labels_2 = ['Purchase order', 'RFQ'];
            const data_2 = {
                labels: labels_2,
                datasets: [
                    {
                        label: 'New',
                        data: result['target_po'],
                        backgroundColor: ['rgb(107, 99, 99)', 'rgb(135, 147, 147)'],
                    }
                ]
            };
            const config_2 = {
                type: 'pie',
                data: data_2,
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: 'Purchase Analysis' }
                    }
                }
            };

            // For Accounting Analysis
            const labels_3 = ['Invoices', 'Bill'];
            const data_3 = {
                labels: labels_3,
                datasets: [
                    {
                        label: 'New',
                        data: result['target_accounting'],
                        backgroundColor: ['rgb(207, 99, 99)', 'rgb(235, 187, 147)'],
                    }
                ]
            };
            const config_3 = {
                type: 'pie',
                data: data_3,
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: 'Accounting Analysis' }
                    }
                }
            };
             const sales_pie = new Chart(document.getElementById('sales_pie'),config_1);
                    const purchase_pie = new Chart(document.getElementById('purchase_pie'),config_2);
                    const account_pie = new Chart(document.getElementById('account_pie'),config_3);
                   return $.when(result);
             }
            // You can use Chart.js or another library to render the charts here.


});
