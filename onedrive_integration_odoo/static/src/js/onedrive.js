odoo.define('onedrive_integration_odoo.dashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var OnedriveDashboard = AbstractAction.extend({
        template: 'OnedriveDashboard',
        events: {
            'click #import': 'synchronize',
            'click #upload': 'upload',
            'click .file-type': 'filter_file_type'
        },
        init() {
            this._super(...arguments);
            var self = this;
            self.synchronize();
        },
        // Calls upload function on click of upload
        upload: function (ev) {
            this.do_action({
                name: "Upload File",
                type: 'ir.actions.act_window',
                res_model: 'upload.file',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        },
        // Appends files retrieved by function(action_synchronize_onedrive) to div onedrive_files on click of import
        synchronize: function (ev) {
            var self = this;
            rpc.query({
                model: 'onedrive.dashboard',
                method: 'action_synchronize_onedrive',
                args: ['']
            }).then(function (result) {
                if (!result) {
                    // Display a notification if access tokens are not set up
                    self.do_action({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': _t('Please setup credentials'),
                            'type': 'warning',
                            'sticky': false,
                        }
                    });
                } else if (result[0] === 'error') {
                    console.log(result);
                    if (result[1] === 'itemNotFound') {
                        // Display a notification if the folder is not found
                        self.do_action({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': _t('Error: Folder not found.'),
                                'type': 'warning',
                                'sticky': false,
                            }
                        });
                    } else {
                        // Display a notification for other errors
                        self.do_action({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': _t('Error:' + result[2]),
                                'type': 'warning',
                                'sticky': false,
                            }
                        });
                    }
                } else {
                    // Empty the onedrive_files div and append the files retrieved
                    self.$('#onedrive_files').empty();
                    var alt_src = "'/onedrive_integration_odoo/static/src/img/file_icon.png'";
                    $.each(Object.keys(result), function (index, name) {
                        self.$('#onedrive_files').append('<div class="col-sm-6 card" align="center"><a href="' + result[name] + '"><img class="card-img-top" src="' + result[name] + '" onerror="this.src=' + alt_src + ';"/></a>' + name + '</div>');
                    });
                }
            });
        },
        filter_file_type: function (ev) {
            var value = ev.currentTarget.getAttribute('value');
            $.each(this.$('.card'), function (index, name) {
                $(this).hide();
                var file_type = (name.textContent).slice(((name.textContent).lastIndexOf(".") - 1 >>> 0) + 2);
                if (file_type == value) {
                    $(this).show();
                }
                if (value == 'allfiles') {
                    $(this).show();
                }
                if (value == 'image') {
                    if (file_type == 'jpeg' || file_type == 'jpg' || file_type == 'png') {
                        $(this).show();
                    }
                }
            });
        },
    });
    core.action_registry.add("onedrive_dashboard", OnedriveDashboard);
    return OnedriveDashboard;
});
