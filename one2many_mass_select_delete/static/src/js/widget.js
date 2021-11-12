odoo.define('one2many_mass_select_delete.form_widgets', function (require) {
	"use strict";

	var core = require('web.core');
	var utils = require('web.utils');
	var fieldRegistry = require('web.field_registry');
	var ListRenderer = require('web.ListRenderer');
	var rpc = require('web.rpc');
	var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
	var _t = core._t;

	ListRenderer.include({
		_updateSelection: function () {
	        this.selection = [];
	        var self = this;
	        var $inputs = this.$('tbody .o_list_record_selector input:visible:not(:disabled)');
	        var allChecked = $inputs.length > 0;
	        $inputs.each(function (index, input) {
	            if (input.checked) {
	                self.selection.push($(input).closest('tr').data('id'));
	            } else {
	                allChecked = false;
	            }
	        });
	        if(this.selection.length > 0){
	        	$('.button_delete_order_lines').show()
	            $('.button_select_order_lines').show()

	        }else{
	        	$('.button_delete_order_lines').hide()
	        	$('.button_select_order_lines').hide()
             }
	        this.$('thead .o_list_record_selector input').prop('checked', allChecked);
	        this.trigger_up('selection_changed', { selection: this.selection });
	        this._updateFooter();
	    },
	})

    var One2manyDelete = FieldOne2Many.extend({
		template: 'One2manyDelete',
		events: {
			"click .button_delete_order_lines": "delete_selected_lines",
			"click .button_select_order_lines": "selected_lines",
		},
		init: function() {
	        this._super.apply(this, arguments);
	    },
		delete_selected_lines: function()
		{
			var self=this;
			var current_model = this.recordData[this.name].model;
			var selected_lines = self.find_deleted_lines();
			if (selected_lines.length === 0)
			{
				this.do_warn(_t("Please Select at least One Record."));
				return false;
			}
			var w_response = confirm("Dou You Want to Delete ?");
			if (w_response) {

                rpc.query({
                    'model': current_model,
                    'method': 'unlink',
                    'args': [selected_lines],
                }).then(function(result){
                    self.trigger_up('reload');
                });
             }
		},
		selected_lines: function()
		{
			var self=this;
			var current_model = this.recordData[this.name].model;
			var selected_lines = self.find_selected_lines();
			if (selected_lines.length === 0)
			{
				this.do_warn(_t("Please Select at least One Record"));
				return false;
			}
			var w_response = confirm("Dou You Want to Select ?");
			if (w_response) {

			rpc.query({
                'model': current_model,
                'method': 'unlink',
                'args': [selected_lines],
            }).then(function(result){
                self.trigger_up('reload');
            });
            }
		},
		_getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
		find_deleted_lines: function () {
            var self=this;
            var selected_list =[];
            this.$el.find('td.o_list_record_selector input:checked')
                    .closest('tr').each(function () {
                        selected_list.push(parseInt(self._getResId($(this).data('id'))));
            });
            return selected_list;
        },

		find_selected_lines: function ()
	   {   var self = this;
           var selected_list =[];
		   var selected_list1 =[];
		   var selected_list2 =[];
	       this.$el.find('td.o_list_record_selector input:checked')
	               .closest('tr').each(function () {
	               	selected_list.push(parseInt(self._getResId($(this).data('id'))));
	       			});
		   if (selected_list.length != 0) {
			   this.$el.find('td.o_list_record_selector')
				   .closest('tr').each(function () {
				   selected_list1.push(parseInt(self._getResId($(this).data('id'))));
			   });
			   selected_list2 = selected_list1.filter(function (x) {
				   return selected_list.indexOf(x) < 0
			   });
		   }
		   return selected_list2;
	   },
    _getResId: function (recordId) {
       var record;
       utils.traverse_records(this.recordData[this.name], function (r) {
       if (r.id === recordId) {
            record = r;
       }
        });
            return record.res_id;
        },

	});
	fieldRegistry.add('one2many_delete', One2manyDelete);
});