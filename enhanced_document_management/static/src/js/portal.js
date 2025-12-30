/** @odoo-module **/


    import publicWidget from "@web/legacy/js/public/public_widget";
    publicWidget.registry.DocumentPortal = publicWidget.Widget.extend({
        selector: '#document_portal',
        events: {
            'click .fa-share': '_onShare',
            'click .re-upload': '_onRequestAccept',
            'click .re-reject': '_onRequestReject',
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

