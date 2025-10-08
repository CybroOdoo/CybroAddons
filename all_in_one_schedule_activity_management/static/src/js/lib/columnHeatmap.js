(function($) {
    $.columnHeatmap = {
        name: 'columnHeatmap',
        version: '1.0',
        release: '2020-06-15',
        author: 'Paulo Kramer',
        site: 'https://www.paulokramer.com',
        documentation: 'https://github.com/PauloAK/jQuery-columnHeatMap'
    };

    $.fn.columnHeatmap = function(options) {
        var settings = $.extend({
            columns: [], // 0 is the first column
            contrast: true, // Change text color to white on stronger background colors
            inverse: false, // By default, higher are red and lower are green, if this options is enabled, the logic are inversed
            animated: true, // Animated background-color and text color transition
            animationSpeed: .1, // Speed of transition animation in seconds
            fn_parseValue: null, // Custom function to parse cell value
            colorStartPoint: 0 // HSL color start point
        }, options);

        try {
            if (!this.is('table'))
                throw 'Selected element isn\'t a table';

            if (settings.columns.length == 0)
                throw 'You need to specify the columns';

            if (settings.colorStartPoint < 0 || settings.colorStartPoint > 360)
                throw `colorStartPoint need to be beetween 0 and 360, current: ${settings.colorStartPoint}`;

            let $table = this;
            let rows = $table.find('tbody tr');
            let data = [];

            $.each(settings.columns, (loop, col) => {
                rows.each((key, row) => {
                    if (key == 0) {
                        data[col.toString()] = new Array;
                        data[col.toString()]['values'] = new Array;
                        data[col.toString()]['tds'] = new Array;
                    }

                    let td = $(row).find('td')[col];
                    data[col.toString()]['tds'].push(td);



                    if (typeof settings.fn_parseValue == "function") {
                        let value = fn_parseValue($(td).text());
                        if (typeof value == "undefined") {
                            throw 'None value returned in fn_parseValue';
                        } else {
                            data[col.toString()]['values'].push(value);
                        }
                    } else {
                        // Get only numbers from the cell, (with float points)
                        let numbers = $(td).text().match(/[\d|\-|.|,]+/)[0];

                        data[col.toString()]['values'].push(parseFloat(numbers));
                    }
                });
            });

            data = data.filter((value) => { return value; });

            $.each(data, (key, col) => {
                if (!col || !col['values'])
                    return;

                data[key]['min'] = null;
                data[key]['max'] = null;

                data[key]['min'] = col['values'].reduce(function(a, b) {
                    return Math.min(a, b);
                });

                data[key]['max'] = col['values'].reduce(function(a, b) {
                    return Math.max(a, b);
                });
            });

            $.each(data, (key, col) => {
                $.each(col['values'], (key, value) => {
                    let colorGenerated = colorGenerator(value, col['min'], col['max']);

                    if (settings.animated) {
                        $(col['tds'][key]).css('transition', `background-color ${settings.animationSpeed}s linear, color ${settings.animationSpeed}s linear`);
                    }

                    $(col['tds'][key]).css('background-color', colorGenerated.color);

                    if (colorGenerated.perc > 70 && settings.contrast) {
                        $(col['tds'][key]).css('color', '#fff');
                    }
                });
            });

            function colorGenerator(value, min, max) {
                var perc = (100 * (value - min)) / (max - min);

                if (settings.inverse)
                    perc = 100 - perc;

                var hsl = Math.abs((perc - 100) * -1) + settings.colorStartPoint;

                return { color: 'hsl(' + hsl + ', 70%, 65%)', perc: perc };
            }
        } catch (error) {
            console.error(`[${$.columnHeatmap.name}::Error] ${error}`);
            return;
        }
    };
}(jQuery));