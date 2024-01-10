odoo.define('odoo_database_restore_manager.dashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var DbRestoreDashboard = AbstractAction.extend({
     template: 'DbRestoreDashboard',
        events: {
        'click #db_restore' : 'restore',
        'change #db_location' : 'filter_location',
        },
        /*  Appends backups retrieved by function(action_import_files) to div db_restore_files */
      init() {
            this._super(...arguments);
            var self=this;
            rpc.query({
              model: 'database.manager',
              method: 'action_import_files',
              args: ['']
            }).then(function(result) {
              if (result[0] == 'error') {
                self.$el.find('.company_image').append('<img src="/logo.png?company=' + result[3] + '"/>')
                self.do_action({
                  'type': 'ir.actions.client',
                  'tag': 'display_notification',
                  'params': {
                    'message': 'Failed to Load Files from ' + result[2] + ' [ ' + result[1] + ' ]',
                    'type': 'warning',
                    'sticky': false,
                  }
                });
              } else {
                var count = 1;
                self.$el.find('.company_image').append('<img src="/logo.png?company=' + result[1] + '"/>')
                _.each(result[0], function(name, index) {
                  var downloadBackup = '';
                  if (['Dropbox', 'OneDrive', 'Google Drive' , 'Nextcloud', 'AmazonS3'].includes(name[1])) {
                    downloadBackup = '<a href="' + name[0] + '"> <button type="button" class="backup_download btn btn-primary"> <i class="fa fa-download o_pivot_download"></i></button></a>';
                  }
                  self.$el.find('.db_restore_files').append('<tr class="file_row table-secondary"><td scope="row" style="text-align:center;">' + count + '</td><td>' + index + '</td><td>' + name[1] + '</td><td>' + name[2] + '</td><td><button type="button" id="db_restore" value=' + name[0] + ' class="btn btn-primary"><i class="fa fa-floppy-o fa-fw"></i> Restore </button>' + downloadBackup + '</td></tr>');
                  count++;
                });
              }
            })
      },
/*  Open up the wizard to restore the selected backup file */
    restore: function(ev) {
      this.do_action({
        name: "Restore Database",
        type: 'ir.actions.act_window',
        res_model: 'database.restore',
        view_mode: 'form',
        view_type: 'form',
        views: [[false, 'form']],
        context: {
          default_db_file: ev.target.getAttribute('value'),
          default_backup_location: this.$(ev.target).closest('tr').find('td').eq(2).text()
        },
        target: 'new',
      });
    },
/*  Filter backups based on storage types */
     filter_location: function(ev) {
      var e = this.$el.find("#db_location").get(0);
      var self = this;
      this.$el.find('.file_row').each(function(index, name) {
        self.$(this).hide();
        var location = self.$(name).find('td').eq(2).text();
        if (e.value === 'all_backups') {
          self.$(this).show();
        } else if (e.value === location) {
          self.$(this).show();
        }
      });
    },
    });
    core.action_registry.add("database_manager_dashboard", DbRestoreDashboard);
    return DbRestoreDashboard;
});
