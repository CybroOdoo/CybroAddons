odoo.define('custom_list_view.serial_no', function (require) {
"use strict";

var core = require('web.core');
var ListRenderer = require('web.ListRenderer');
var _t = core._t;

ListRenderer.include({

	_getNumberOfCols: function () {
		var columns = this._super();
		columns +=1;
		return columns;
    },


    _renderFooter: function () {
        const $footer = this._super.apply(this, arguments);
        $footer.find('tr').prepend($('<td>'));
        return $footer;
    },

    _renderHeader: function () {
        var $thead = this._super.apply(this, arguments);
        if (this.hasSelectors) {
            $thead.find('th.o_list_record_selector').before($('<th>', {class: 'o_list_serial_number_header'}).html('SI.NO'));
        }
        return $thead;
    },
    _renderRow: function (record) {
         var $rows = this._super(record);
    	 var index = this.state.data.indexOf(record)
	    	if (this.hasSelectors) {
	    		$rows.prepend($("<th class='o_list_serial_number'>").html(index+1));
    	}
    	return $rows;
    },
});
});