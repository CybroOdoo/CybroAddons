odoo.define('website_documents', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');

     publicWidget.registry.documentUploadButton = publicWidget.Widget.extend({
        selector: 'div[id="document_upload_button"]',
        events: {
            'click #web_docs_upload': '_onUploadButtonClick',
        },
        _onUploadButtonClick: function(){
            /**
                * Method to open the document upload modal
                * $('#docs_upload_form').modal('show'); this method will open the modal
                * the modal located in another template, so that we used JQUERY to open modal
            */
            var self = this;
            this.$el.find('#docs_upload_form').modal('show');
            rpc.query({
                   model : 'document.workspace',
                   method : 'work_spaces',
                   args : []
            }).then(function(result){
               result.forEach(element =>{
                 self.$el.find('#workspace').append(`
                    <option value="${element['id']}">${element['name']}</option>`
                 )
               })
            })
        }
    })
})
