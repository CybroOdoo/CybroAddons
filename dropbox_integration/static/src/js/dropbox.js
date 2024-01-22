/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState,useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");

export class DropboxDashboard extends Component{
     setup() {
        super.setup(...arguments);
        this.orm = useService('orm')
        this.user = useService("user");
        this.actionService = useService("action");
        this.rootRef = useRef("root");
         var self = this;
        onWillStart(async () => {
            await this.fetch_data();
        });
     }
     /*  Appends files retrieved by function(import_files) to div files */
     async fetch_data(){
          var self = this.actionService;
          this.orm.call('dropbox.dashboard','action_import_files',['']
                ).then(function (result) {
                    if(result[0]=='e')
                    {
                        self.doAction({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                    'message': 'Failed to Load Files [ '+result[1]+' ]',
                                    'type': 'warning',
                                    'sticky': false,
                            }
                        })
                    }
                    else if(!result){
                        self.doAction({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                    'message': 'Please setup Access Token',
                                    'type': 'warning',
                                    'sticky': false,
                            }
                        })
                    }
                    else{
                         $('#files').empty();
                         var alt_src = "'dropbox_integration/static/src/img/file.png'"
                         $.each(Object.keys(result),function(index, name){
                         $('#files').append('<div class="col-sm-6 card dropbox_card" align="center"><a class="card-image-text dropbox_text" href="'+result[name]+'"><img class="card-img-top drop_box_image" align="center" src="'+result[name]+'" onerror="this.src='+alt_src+';"/<br/><br/>'+name+'</a></div>');
                          });
                    }
                });
     }
         /* Calls upload function on click of upload */
     upload(ev) {
            var self = this;
           self.actionService.doAction({
              name: "Upload to Dropbox",
              type: 'ir.actions.act_window',
              res_model: 'dropbox.upload',
              view_mode: 'form',
              view_type: 'form',
              views: [[false, 'form']],
              target: 'new',
          });
     }
     /* Search console function */
     search_file (ev) {
        var value = $('.header-search-input').val().toLowerCase()
        $('.card').filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
     }
}
DropboxDashboard.template = "DropboxDashboard"
registry.category("actions").add("dropbox_dashboard", DropboxDashboard)
