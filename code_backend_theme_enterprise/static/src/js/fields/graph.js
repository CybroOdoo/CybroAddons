odoo.define('code_backend_theme_enterprise.graph', function (require) {
    "use strict";

    var GraphRenderer = require('web.GraphRenderer');

    var MyCOLORS = ["#556ee6", "#f1b44c", "#50a5f1", "#ffbb78", "#34c38f", "#98df8a", "#d62728",
        "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", "#e377c2", "#f7b6d2",
        "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", "#17becf", "#9edae5"];
    var MyCOLOR_NB = MyCOLORS.length;

    function hexToRGBA(hex, opacity) {
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        var rgb = result.slice(1, 4).map(function (n) {
            return parseInt(n, 16);
        }).join(',');
        return 'rgba(' + rgb + ',' + opacity + ')';
    }

    return GraphRenderer.include({

        _getMyColor: function (index) {
            return MyCOLORS[index % MyCOLOR_NB];
        },

        _renderBarChart: function (dataPoints) {
            var self = this;

            // prepare data
            var data = this._prepareData(dataPoints);

            data.datasets.forEach(function (dataset, index) {
                // used when stacked
                dataset.stack = self.state.stacked ? self.state.origins[dataset.originIndex] : undefined;
                // set dataset color
                var color = self._getMyColor(index);
                dataset.backgroundColor = color;
            });

            // prepare options
            var options = this._prepareOptions(data.datasets.length);

            // create chart
            var ctx = document.getElementById(this.chartId);
            this.chart = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: options,
            });
        },

        _renderLineChart: function (dataPoints) {
            var self = this;

            // prepare data
            var data = this._prepareData(dataPoints);
            data.datasets.forEach(function (dataset, index) {
                if (self.state.processedGroupBy.length <= 1 && self.state.origins.length > 1) {
                    if (dataset.originIndex === 0) {
                        dataset.fill = 'origin';
                        dataset.backgroundColor = hexToRGBA(MyCOLORS[0], 0.4);
                        dataset.borderColor = hexToRGBA(MyCOLORS[0], 1);
                    } else if (dataset.originIndex === 1) {
                        dataset.borderColor = hexToRGBA(MyCOLORS[1], 1);
                    } else {
                        dataset.borderColor = self._getMyColor(index);
                    }
                } else {
                    dataset.borderColor = self._getMyColor(index);
                }
                if (data.labels.length === 1) {
                    // shift of the real value to right. This is done to center the points in the chart
                    // See data.labels below in Chart parameters
                    dataset.data.unshift(undefined);
                }
                dataset.pointBackgroundColor = dataset.borderColor;
                dataset.pointBorderColor = 'rgba(0,0,0,0.2)';
            });
            if (data.datasets.length === 1) {
                const dataset = data.datasets[0];
                dataset.fill = 'origin';
                dataset.backgroundColor = hexToRGBA(MyCOLORS[0], 0.4);
            }

            // center the points in the chart (without that code they are put on the left and the graph seems empty)
            data.labels = data.labels.length > 1 ?
                data.labels :
                Array.prototype.concat.apply([], [[['']], data.labels, [['']]]);

            // prepare options
            var options = this._prepareOptions(data.datasets.length);

            // create chart
            var ctx = document.getElementById(this.chartId);
            this.chart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: options,
            });
        },
    });
});