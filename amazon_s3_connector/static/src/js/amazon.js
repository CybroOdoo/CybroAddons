/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

export class AmazonDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm');
        this.user = useService("user");
        this.actionService = useService("action");
        this.rootRef = useRef("root");

        onWillStart(async () => {
            await this.fetch_data();
        });
    }
     /*  Appends files retrieved by function(import_files) to div files */
    async fetch_data() {
            var self = this.actionService;
            this.orm.call('amazon.dashboard','amazon_view_files',['']
            ).then(function (result) {
            if (!result) {
                    self.doAction({
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Please Setup The Access Keys',
                        'type': 'warning',
                        'sticky': false,
                    }
                });
            } else if (result[0] === 'e') {
                self.doAction({
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Failed to Load Files [ ' + result[1] + ' ]',
                        'type': 'warning',
                        'sticky': false,
                    }
                });
            }
            else{
                $('.amazon_s3_files').empty();
                var count=1;
                $.each(result,function(index, name){
                $('.amazon_s3_files').append('<tr class="file_row table-secondary"><td scope="row" style="text-align:center;">'+count+'</td><td><a class="file_name" href="'+name[1]+'"</a>'+name[0]+'<i class="fa fa-download download_file"></i></td><td>'+name[2]+'</td><td>'+name[3]+'</td><td>'+name[4]+'</td></tr>');
                count ++;
                });
                }
              });
    }
    /* Sort file names in ascending */
    sort_name(ev) {
      var table = $("#files_table tbody");
      var rows = table.find("tr").toArray();

      rows.sort(function(a, b) {
        var x = $(a).find("td:eq(1)").text().toLowerCase();
        var y = $(b).find("td:eq(1)").text().toLowerCase();
        return x.localeCompare(y);
      });
      table.append(rows);
    }
    /* Calls upload function on click of upload */
    upload(ev) {
            var self = this;
            self.actionService.doAction({
                name: "Upload File",
                type: 'ir.actions.act_window',
                res_model: 'amazon.upload.file',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                });
       }
        /* Sort Number function */
        sort_number(ev){
        var sorted = $('#files_table tbody tr').sort(function(a, b) {
        var a = $(a).find('td:first').text(), b = $(b).find('td:first').text();
        return a.localeCompare(b, false, {numeric: true})
        })
        $('#files_table tbody').html(sorted)
    }
         /* Search console function */
        search_file (ev) {
        var value = $('.amazon_header-search-input').val().toLowerCase()
        $('.file_row').filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
     }

    /* Filter on basis of file type */
    filter_files(ev) {
      var e = $("#filter").get(0);
      $('.file_row').each(function(index, name) {
        $(this).hide();
        var file_name = $(name).find('a').text();
        var file_type = file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2);
        if (e.value === 'ALL FILES') { $(this).show(); }
        else if (e.value === file_type) { $(this).show(); }
        else if (e.value === 'image') {
          if (file_type === 'jpeg' || file_type === 'jpg' || file_type === 'png') {
            $(this).show();
          }
        } else if (e.value === 'txt') {
          if (file_type === 'txt' || file_type === 'docx') {
            $(this).show();
          }
        }
      });
    }
}

AmazonDashboard.template = "AmazonDashboard";
registry.category("actions").add("amazon_dashboard", AmazonDashboard);
