odoo.define('code_backend_theme_enterprise.fields', function (require) {
    "use strict";

    var basic_fields = require("web.basic_fields");

    //Changing Sales Team Graph color
    var SalesTeamGraph = basic_fields.JournalDashboardGraph.include({

        _getBarChartConfig: function () {
            this._super();
            var data = [];
            var labels = [];
            var backgroundColor = [];

            this.data[0].values.forEach(function (pt) {
                data.push(pt.value);
                labels.push(pt.label);
                var color = pt.type === 'past' ? '#ccbdc8' : (pt.type === 'future' ? '#f1b44c' : '#556ee6');
                backgroundColor.push(color);
            });
            return {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        fill: 'start',
                        label: this.data[0].key,
                        backgroundColor: backgroundColor,
                    }]
                },
                options: {
                    legend: {display: false},
                    scales: {
                        yAxes: [{display: false}],
                    },
                    maintainAspectRatio: false,
                    tooltips: {
                        intersect: false,
                        position: 'nearest',
                        caretSize: 0,
                    },
                    elements: {
                        line: {
                            tension: 0.000001
                        }
                    },
                },
            };
        },
    });
});

