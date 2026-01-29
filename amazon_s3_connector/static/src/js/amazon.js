odoo.define('amazon_s3_connector.dashboard', function(require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var AmazonDashboard = AbstractAction.extend({
        template: 'AmazonDashboard',
        events: {
            'click #amazon_s3_upload': 'upload',
            'click .sort-name': 'sort_name',
            'click .sort-number': 'sort_number',
            'change #filter': 'filter_files',
            'keyup .amazon_header-search-input': 'search_filtered_files'
        },
        /* Load files to dashboard from s3 */
        init() {
            this._super(...arguments);
            var self = this;
            rpc.query({
                model: 'amazon.dashboard',
                method: 'amazon_view_files',
                args: ['']
            }).then(function(result) {
                if (!result) {
                    self.do_action({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Please Setup The Access Keys',
                            'type': 'warning',
                            'sticky': false,
                        }
                    })
                } else if (result[0] == 'e') {
                    self.do_action({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Failed to Load Files [ ' + result[1] + ' ]',
                            'type': 'warning',
                            'sticky': false,
                        }
                    })
                } else {
                    self.$('.amazon_s3_files').empty();
                    var count = 1;
                    $.each(result, function(index, name) {
                        self.$el.find('.amazon_s3_files').append('<tr class="file_row table-secondary"><td scope="row" style="text-align:center;">' + count + '</td><td><a class="file_name" href="' + name[1] + '"</a>' + name[0] + '<i class="fa fa-download download_file"></i></td><td>' + name[2] + '</td><td>' + name[3] + '</td><td>' + name[4] + '</td></tr>');
                        count++;
                    });
                }
            });
        },
        /* Sort file names in ascending */
        sort_name: function(ev) {
            var table = this.$el.find("#files_table tbody");
            var rows = table.find("tr").toArray();
            rows.sort(function(a, b) {
                var x = $(a).find("td:eq(1)").text().toLowerCase();
                var y = $(b).find("td:eq(1)").text().toLowerCase();
                return x.localeCompare(y);
            });
            table.append(rows);
        },
        /* Sort Serial Numbers in ascending */
        sort_number: function(ev) {
            var sorted = this.$('#files_table tbody tr').sort(function(a, b) {
                var a = $(a).find('td:first').text(),
                    b = $(b).find('td:first').text();
                return a.localeCompare(b, false, {
                    numeric: true
                })
            })
            this.$el.find('#files_table tbody').html(sorted)
        },
        /* Upload files to amazon s3 */
        upload: function(ev) {
            /* calls wizard action */
            this.do_action({
                name: "Upload File",
                type: 'ir.actions.act_window',
                res_model: 'amazon.upload.file',
                view_mode: 'form',
                view_type: 'form',
                views: [
                    [false, 'form']
                ],
                target: 'new',
            });
        },
        /* Search console function */
        search_filtered_files: function(ev) {
            var value = this.$('.amazon_header-search-input').val().toLowerCase();

            if (ev.type === 'keypress' && ev.key !== 'Enter') {
                // Check if the pressed key is Backspace
                if (ev.key === 'Backspace') {
                    // If Backspace was pressed and the input is empty, show all rows
                    this.$el.find('.amazon_header-search-input').val('');
                    this.$el.find('.file_row').show();
                    this.$el.find("#filter").val("ALL FILES");
                }
                return;
            }
            // If the value is empty, show all rows
            if (value === '') {
                this.$el.find('.file_row').show();
                this.$el.find("#filter").val("ALL FILES");
            } else {
                this.$el.find('.file_row:visible').each(function(index, row) {
                    var $row = $(row);
                    if ($row.text().toLowerCase().indexOf(value) > -1) {
                        $row.show();
                    } else {
                        $row.hide();
                    }
                });
            }
        },
        /* Filter on basis of file type */
        filter_files: function(ev) {
            var self = this;
            var element = this.$el.find("#filter").get(0);
            var visibleRowCount = 0; // To keep track of visible rows
            this.$el.find('.file_row').each(function(index, row) {
                var $row = $(row);
                var serialNumberCell = $row.find('td:first-child'); // Assuming the serial number cell is the first cell
                $row.hide();
                var file_name = $row.find('a').text();
                var file_type = file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2);
                if (element.value === 'ALL FILES' ||
                    (element.value === 'image' && (file_type === 'jpeg' || file_type === 'jpg' || file_type === 'png')) ||
                    (element.value === 'txt' && (file_type === 'txt' || file_type === 'docx')) ||
                    element.value === file_type) {
                    $row.show();
                    visibleRowCount++;
                    serialNumberCell.text(visibleRowCount); // Update serial number
                }
            });
        },
    });
    core.action_registry.add("amazon_dashboard", AmazonDashboard);
    return AmazonDashboard;
});