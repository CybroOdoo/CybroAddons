odoo.define('web.one2many_mass_select_delete', function(require) {
    "use strict";
    var Model = require('web.Model');
    var core = require('web.core');
    var delete_on2many = core.form_widget_registry.get('one2many');
	var _t = core._t;
	
    var One2manyDelete = delete_on2many.extend({
        template: 'One2manyDelete',
		multi_selection: true,

		init: function() {
	        this._super.apply(this, arguments);
	    },

		render_value: function ()
		{
			this._super.apply(this, arguments);
            var self=this;
			if (this.get('readonly')) {
				self.$('.mass_delete_buttons').hide();
			}
			else{
				self.$('.mass_delete_buttons').show();
			}
			self.$el.find(".button_mass_delete").click(function(){
					self.delete_selected_lines();
	        });
			self.$el.find(".button_mass_select").click(function(){
	        	self.selected_lines();
	        });
		},

	   delete_selected_lines: function()
	   {
		var self = this;
		var current_model = new Model(this.dataset.model);
		var selected_lines = self.find_deleted_lines();
		if (selected_lines.length === 0) {
			this.do_warn(_t("Please Select at least One Record.!"));
			return false;
		}
	   var w_response = confirm("Dou you want to delete.?");
			if (w_response) {
				current_model.call('unlink', [selected_lines], {context: self.dataset.context})
					.then(function () {
						window.location.reload()
					});
			}

	   },

		selected_lines: function()
	   {
			var self = this;
	    	var current_model = new Model(this.dataset.model);
			var select_lines = self.find_selected_lines();
			if (select_lines.length === 0)
			{
		    	this.do_warn(_t("Please Select at least One Record"));
		    	return false;
			}
		   var w_response = confirm("Dou You Want to Select");
			if (w_response) {
				current_model.call('unlink', [select_lines], {context: self.dataset.context})
					.then(function (result) {
						window.location.reload()
					});
			}
	   },

	   find_deleted_lines: function ()
	   {
	       var selected_list =[];
	       this.$el.find('td.o_list_record_selector input:checked')
	               .closest('tr').each(function () {
	               	selected_list.push(parseInt($(this).context.dataset.id));
	       });
	       return selected_list;
	   },

		find_selected_lines: function ()
	   {
	       var selected_list =[];
		   var selected_list1 =[];
		   var selected_list2 =[];
	       this.$el.find('td.o_list_record_selector input:checked')
	               .closest('tr').each(function () {
	               	selected_list.push(parseInt($(this).context.dataset.id));
	       			});
		   if (selected_list.length != 0) {
			   this.$el.find('td.o_list_record_selector')
				   .closest('tr').each(function () {
				   selected_list1.push(parseInt($(this).context.dataset.id));
			   });
			   selected_list2 = selected_list1.filter(function (x) {
				   return selected_list.indexOf(x) < 0
			   });
		   }
		   return selected_list2;
	   },

		process_modifiers: function () {
			var self = this;
			this._super();
			if (this.get('readonly')) {
				self.$('.mass_delete_buttons').hide();
			}
			else{
				self.$('.mass_delete_buttons').show();
			}
			}

	});

    core.form_widget_registry.add('one2many_delete', One2manyDelete);
    return {
        One2manyDelete: One2manyDelete
    };
});
