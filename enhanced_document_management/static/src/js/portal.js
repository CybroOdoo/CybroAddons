odoo.define("document.my_portal", function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    publicWidget.registry.DocumentPortal = publicWidget.Widget.extend({
        selector: 'div[id="document_portal"]',
        events: {
            'click .fa-share': '_onShare',
            'click .re-upload': '_onRequestAccept',
            'click .re-reject': '_onRequestReject',
        },
        _onShare: function(ev){
            /**
                * Method to copy sharable link
            */
            var record_url = ev.target.dataset.url
            var $temp = $("<input>");
            $("body").append($temp);
            $temp.val(record_url).select();
            document.execCommand("copy");
            $temp.remove();
            this.$el.find('.toast').addClass('show');
            this.$el.find('.toast-body').text(record_url)
        },
        _onRequestAccept: function(ev){
            /**
            * Function to open file upload modal
            */
            this.$el.find('#req_upload_form').modal('show');
            this.$el.find('#workspace').val(ev.target.dataset.workspace)
            this.$el.find('#requested_by').val(ev.target.dataset.requested_by)
            this.$el.find('#workspace_id').val(ev.target.dataset.workspace_id)
            this.$el.find('#rec_id').val(ev.target.dataset.id)
        },
        _onRequestReject: function(ev){
            /**
            * Function to reject file upload request
            */
            this.$el.find('#req_id').val(ev.target.dataset.id)
            this.$el.find('#req_reject_form').modal('show');
        }

    })
})
