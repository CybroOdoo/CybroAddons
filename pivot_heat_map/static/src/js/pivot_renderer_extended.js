odoo.define('pivot_heat_map.renderer', function (require) {
    "use strict";

    var PivotRenderer = require('web.PivotRenderer');
    var field_utils = require('web.field_utils');
    var core = require('web.core');

    var _t = core._t;

    PivotRenderer.include({
        get_total_col: function(rows, indent, col){
            var total = 0;
            _.each(rows, function(rec){
                if(indent == rec.indent && rec.values[col]){
                    total += rec.values[col];
                }
            });
            return total;
        },
        get_total_row: function(values, row, col){
            var total = 0;
            var measures = this.state.measures.length;

            for (var i=col;i<values.length-measures;i+=measures){
                total += values[i] ? values[i] : 0;
            }
            for (var i=col-measures;i>=0;i-=measures){
                total += values[i] ? values[i] : 0;
            }
            return total;
        },

        get_parent_index: function(indent, row, col){
            var rows = this.state.rows;
            for (var i=row-1;i>=0;i--){
                if(rows[i].indent == indent-1){
                    return (indent-1)+'-'+i+'-'+col;
                }
            }
        },
        get_bg_color: function(value, row, col, indent){
            var index = indent+'-'+row+'-'+col;
            if (value != 'undefined'){
                if(index in this.cells){
                    return 'rgb(250,'+this.cells[index]+','+this.cells[index]+')';
                }
            }
            else{
                this.cells[index] = null;
                return null;
            }
        },
        get_base_value: function(row, col, measures){
            for(var j=row.values.length-measures;j<row.values.length;j++){
                if((j - col)%measures == 0){
                    return j;
                }
            }
        },
        update_cell_colors: function(rows){
            var self = this;
            var i,j,index,cols,row,value,total,parent_index,base,color_code,cells,measures;
            if(rows){
                cols = rows[0].values.length;
                cells = this.cells;
                measures = this.state.measures.length;
                switch(self.heat_map){
                    case 'col': {
                        for(i=0;i<rows.length;i++){
                            row = rows[i];
                            for(j=0;j<cols;j++){
                                value = row.values[j];
                                if(value != 'undefined'){
                                    index = row.indent+'-'+i+'-'+j;
                                    if(!(index in cells)){
                                        if(row.indent==0){
                                            /*first row*/
                                            cells[index] = 90;
                                            continue;
                                        }
                                        /*other rows*/
                                        total = self.get_total_col(rows, row.indent, j);
                                        parent_index = self.get_parent_index(row.indent, i, j);
                                        base = (parent_index && cells[parent_index]) ? cells[parent_index] : 90;
                                        color_code = Math.floor(base + 165*(total - Math.abs(value))/total);
                                        cells[index] = color_code;
                                    }
                                }

                            }
                        }
                        break;
                    }
                    case 'row': {
                        for(i=0;i<rows.length;i++){
                            row = rows[i];
                            for(j=0;j<cols;j++){
                                value = row.values[j];
                                if(value != 'undefined'){
                                    index = row.indent+'-'+i+'-'+j;
                                    if(!(index in cells)){
                                        if(j >= cols-measures){
                                            cells[index] = 90;
                                            continue;
                                        }
                                        /*other rows*/
                                        total = self.get_total_row(row.values, i, j);

                                        color_code = Math.floor(90 + 165*(total - Math.abs(value))/total);
                                        cells[index] = color_code;
                                    }
                                }

                            }
                        }
                        break;
                    }
                    case 'both': {
                        /*setting first row and last columns as base*/
                        for(i=0;i<rows.length;i++){
                            row = rows[i];
                            for(j=cols-1;j>=0;j--){
                                value = row.values[j];
                                if(value != 'undefined'){
                                    index = row.indent+'-'+i+'-'+j;
                                    if(!(index in cells)){
                                        if((j >= cols-measures) && i==0){
                                            cells[index] = 90;
                                            continue;
                                        }
                                        else if(j >= cols-measures){
                                            total = self.get_total_col(rows, row.indent, j);
                                            parent_index = self.get_parent_index(row.indent, i, j);
                                            base = (parent_index && cells[parent_index]) ? cells[parent_index] : 90;
                                            color_code = Math.floor(base + 165*(total - Math.abs(value))/total);
                                            cells[index] = color_code;
                                        }
                                        else{
                                            total = self.get_total_row(row.values, i, j);
                                            var parent_col = self.get_base_value(row, j, measures);
                                            parent_index = parent_col ? (row.indent+'-'+i+'-'+parent_col):null;
                                            base = parent_index ? cells[parent_index] : 90;
                                            color_code = Math.floor(base + 165*(total - Math.abs(value))/total);
                                            cells[index] = color_code;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                this.cells = cells;
            }
        },
        _renderRowsHeat: function ($tbody, rows) {
            var self = this;
            /*setting cell colors*/
            this.update_cell_colors(rows);
            var i, j, value, measure, name, $row, $cell, $header;
            var nbrMeasures = this.state.measures.length;
            var length = rows[0].values.length;
            var shouldDisplayTotal = this.state.mainColWidth > 1;
            var groupbyLabels = _.map(this.state.rowGroupBys, function (gb) {
                return self.state.fields[gb.split(':')[0]].string;
            });
            var measureTypes = this.state.measures.map(function (name) {
                return self.state.fields[name].type;
            });
            for (i = 0; i < rows.length; i++) {
                $row = $('<tr>');
                $header = $('<td>')
                    .text(rows[i].title)
                    .data('id', rows[i].id)
                    .css('padding-left', (5 + rows[i].indent * 30) + 'px')
                    .addClass(rows[i].expanded ? 'o_pivot_header_cell_opened' : 'o_pivot_header_cell_closed');
                if (rows[i].indent > 0) $header.attr('title', groupbyLabels[rows[i].indent - 1]);
                $header.appendTo($row);
                for (j = 0; j < length; j++) {
                    value = rows[i].values[j];
                    if (value !== undefined) {
                        name = this.state.measures[j % nbrMeasures];
                        measure = this.state.fields[name];
                        value = field_utils.format[measureTypes[j % nbrMeasures]](value, measure);
                    }
                    /*fetching background color*/
                    var bg_color = null;
                    if (value){
                        bg_color = self.get_bg_color(value, i, j, rows[i].indent);
                    }

                    $cell = $('<td>')
                                .data('id', rows[i].id)
                                .data('col_id', rows[i].col_ids[Math.floor(j / nbrMeasures)])
                                .toggleClass('o_empty', !value)
                                .text(value)
                                .addClass('o_pivot_cell_value text-right');
                    if(bg_color != null){
                        $cell.css({'background-color': bg_color});
                    }
                    if (((j >= length - this.state.measures.length) && shouldDisplayTotal) || i === 0){
                        $cell.css('font-weight', 'bold');
                    }
                    $row.append($cell);

                    $cell.toggleClass('hidden-xs', j < length - nbrMeasures);
                }
                $tbody.append($row);
            }
        },

        _renderRows: function ($tbody, rows) {
            var self = this;
            if(this.heat_map != null){
                self._renderRowsHeat($tbody, rows);
            }
            else{
                this._super($tbody, rows);
            }
        }
    });
});
