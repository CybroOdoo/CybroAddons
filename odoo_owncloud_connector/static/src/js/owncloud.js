odoo.define('odoo_owncloud_connector.dashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var OwncloudDashboard = AbstractAction.extend({
     template: 'OwncloudDashboard',
        events: {
          'click #owncloud_export' : 'export',
          'click #owncloud_import' : 'import',
          'click .delete_file': 'delete_file',
          'change #owncloud_filter' : 'filter_files',
          'keyup .owncloud_header-search-input' : 'search_file'
        },
        /*  Appends files retrieved by function(owncloud_view_files) to owncloud_table */
        init() {
            this._super(...arguments);
            var self = this;
            self.import();
        },
         import: function(ev) {
            var self = this;
            rpc.query({
                    model: 'owncloud.dashboard',
                    method: 'action_owncloud_view_files',
                 }).then(function (result) {
                    if(result[0]=='e'){
                        self.do_action({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                    'message': 'Failed to Load Files [ '+result[1]+' ]',
                                    'type': 'warning',
                                    'sticky': false,
                                    }
                            })
                    } else {
                        self.$el.find('.owncloud_files').empty();
                        var count=1;
                            result.forEach((name, index) => {
                                self.$('.owncloud_files').append('<tr class="file_row table-secondary"><td scope="row" style="text-align:center;">'+count+'</td><td><a class="file_name" href="'+name[1]+'"</a>'+name[0]+'<i class="fa fa-download download_file"></i></td><td>'+name[2]+'</td><td>'+name[3]+'</td><td id="delete_file" value="'+name[0]+'" ><i class="fa fa-trash delete_file" style="cursor: pointer;"></i></td></tr>');
                                count ++;
                        });
                     }
                 });
        },
        /* Calls wizard action */
        export: function (ev) {
            var self = this
                rpc.query({
                model: 'owncloud.upload',
                method: 'credentials_checking',
                args:[,]
            }).then(function (result) {
                if (result == true){
                    self.do_action({
                        name: "Upload File",
                        type: 'ir.actions.act_window',
                        res_model: 'owncloud.upload',
                        view_mode: 'form',
                        view_type: 'form',
                        views: [[false, 'form']],
                        target: 'new',
                        });
                } else {
                    Dialog.alert(self, ("Please Configure the credentials."));
                }
                })
       },
        /* Delete the file */
        delete_file: function (ev){
            var self = this
            rpc.query({
                model: 'owncloud.dashboard',
                method: 'action_delete_files',
                args:['', ev.target.parentNode.getAttribute('value')]
            }).then(function (result) {
                if(result[0]=='e'){
                    self.do_action({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Failed to Delete File [ '+result[1]+' ]',
                            'type': 'warning',
                            'sticky': false,
                        }
                    })
           } else {
               self.do_action({
                   'type': 'ir.actions.client',
                   'tag': 'display_notification',
                   'params': {
                        'message': 'File deleted successfully',
                        'type': 'success',
                        'sticky': false,
                   }
               })
               ev.target.parentNode.parentNode.remove()
               self.sort();
                }
            });
        },
        /* Sort the files */
        sort: function() {
            var table = this.$el.find("#files_table");
            var tbody = table.find("tbody");
            var rows = tbody.find("tr");
            rows.sort(function(a, b) {
                var slNoA = parseInt($(a).find("td:eq(0)").text());
                var slNoB = parseInt($(b).find("td:eq(0)").text());
                return slNoA - slNoB;
            });
            var updated_rows = []
            for(var i=0;i<rows.length;i++){
                if(rows[i].style.display == false){
                    updated_rows.push(rows[i])
                }
            }
            $.each(updated_rows, function(index, row) {
                tbody.append(row);
                $(row).find("td:eq(0)").text(index + 1);
            });
        },
        /* Search console function */
        search_file: function (ev) {
        var self = this
        var value = this.$el.find('.owncloud_header-search-input').val().toLowerCase();
            // If the value is empty, show all rows
            if (value === '') {
                this.$el.find('.file_row').show();
                this.$el.find("#filter").val("ALL FILES");
                self.sort();
            }
            else if (ev.key === 'Backspace') {
                    // If Backspace was pressed and the input is empty, show all rows
                    this.$el.find('.owncloud_header-search-input').clearInputs();
                    this.filter_files();
                    self.sort();
            }
             else {
                this.$el.find('.file_row:visible').each(function(index, row) {
                    var row = $(row);
                    if (row.text().toLowerCase().indexOf(value) > -1) {
                        row.show();
                        self.sort();
                    } else {
                        row.hide();
                        self.sort();
                    }
                });

            }
        },
        /* Filter on basis of file type */
        filter_files: function(ev){
               self = this
               var filter = this.$el.find('#owncloud_filter')[0];
               this.$el.find('.file_row').each(function(index, name){
                  self.$(this).hide();
                  var file_name = self.$el.find('a')[index].innerText;
                  var file_type = file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2);
                     if (filter.value=='ALL FILES'){
                        self.$(this).show();
                         }
                     else if (filter.value == file_type){
                        self.$(this).show();
                         }
                     else if(filter.value == 'image'){
                          if (file_type=='jpeg' || file_type=='jpg' || file_type=='png'){
                                self.$(this).show();
                            }
                        }
                     else if(filter.value == 'txt'){
                          if (file_type=='txt' || file_type=='docx'){
                               self.$(this).show();
                             }
                        }
               });
               self.sort();
        },
      });
    core.action_registry.add("owncloud_dashboard", OwncloudDashboard);
    return OwncloudDashboard;
});
