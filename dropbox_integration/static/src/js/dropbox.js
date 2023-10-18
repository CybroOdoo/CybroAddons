odoo.define('dropbox_integration.dashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var DropboxDashboard = AbstractAction.extend({
     template: 'DropboxDashboard',
        events: {
        'click #upload' : 'upload',
        'keyup .header-search-input' : 'search_file'
        },
        /*  Appends files retrieved by function(import_files) to div files */
       init() {
          this._super(...arguments);
            var self = this;
            rpc.query({
                    model: 'dropbox.dashboard',
                    method: 'action_import_files',
                    args:['']
                 }).then(function (result) {
                    if(result[0]=='error')
                       {
                        self.do_action({
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
                        self.do_action({
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
                     self.$('#files').empty();
                     var alt_src = "'dropbox_integration/static/src/img/file.png'"
                     $.each(Object.keys(result),function(index, name){
                     self.$('#files').append('<div class="col-sm-6 card dropbox_card" align="center"><a class="card-image-text dropbox_text" href="'+result[name]+'"><img class="card-img-top drop_box_image" align="center" src="'+result[name]+'" onerror="this.src='+alt_src+';"/<br/><br/>'+name+'</a></div>');
                      });
                      }
                });
       },
       /* Calls upload function on click of upload */
       upload: function (ev) {
           this.do_action({
              name: "Upload to Dropbox",
              type: 'ir.actions.act_window',
              res_model: 'dropbox.upload',
              view_mode: 'form',
              view_type: 'form',
              views: [[false, 'form']],
              target: 'new',
          });
       },
      /* Search console function */
      search_file: function (ev) {
        var value = this.$('.header-search-input').val().toLowerCase()
        var cards = this.$('.card');
        Array.from(cards).forEach(function (card) {
            card.style.display = card.textContent.toLowerCase().indexOf(value) > -1 ? 'block' : 'none';
        });
      },
      });
    core.action_registry.add("dropbox_dashboard", DropboxDashboard);
    return DropboxDashboard;
});
