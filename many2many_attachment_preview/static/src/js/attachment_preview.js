odoo.define("many2many_attachment_preview.attachment_preview", function(require) {
    "use strict";
    var AbstractField = require("web.AbstractField");
    var field_registry = require("web.field_registry");
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    var many2many_preview = AbstractField.extend({
        template: "FieldBinaryFileUploader",
        template_files: "PdcDocument.files",
        supportedFieldTypes: ['many2many'],
        fieldsToFetch: {
            name: {
                type: 'char'
            },
            mimetype: {
                type: 'char'
            },
        },
        events: {
            'click .o_attach': '_onAttach',
            'click .o_attachment_delete': '_onDelete',
            'change .o_input_file': '_onFileChanged',
            'click .o_image_box': '_onFilePDF',
            'click .pdc_close': '_onClosePreview', // Add event for close button
        },
        /**
         * Initializes the widget.
         *
         * @constructor
         */
        init: function() {
            this._super.apply(this, arguments);

            if (this.field.type !== 'many2many' || this.field.relation !== 'ir.attachment') {
                var msg = _t("The type of the field '%s' must be a many2many field with a relation to 'ir.attachment' model.");
                throw _.str.sprintf(msg, this.field.string);
            }

            this.uploadedFiles = {};
            this.uploadingFiles = [];
            this.fileupload_id = _.uniqueId('oe_fileupload_temp');
            $(window).on(this.fileupload_id, this._onFileLoaded.bind(this));

            this.metadata = {};
            this.previewOpen = {}; // Object to track open previews for each attachment
        },
        /**
         * Cleans up resources when the widget is destroyed.
         */
        destroy: function() {
            this._super();
            $(window).off(this.fileupload_id);
        },

        _getFileId: function(attachment) {
            return attachment.id
        },
        _getId: function(attachment) {
            return attachment.attributes[1].value
        },
        _generatedMetadata: function() {
            var self = this;
            _.each(this.value.data, function(record) {
                self.metadata[record.id] = {
                    allowUnlink: self.uploadedFiles[record.data.id] || false,
                    FileId: self._getFileId(record.data)
                };
                self.previewOpen[record.id] = false; // Initialize preview flag for each attachment
            });
        },
        /**
         * Renders the widget.
         */
        _render: function() {
            this._generatedMetadata();
            this.$('.oe_placeholder_files, .o_attachments')
                .replaceWith($(qweb.render(this.template_files, {
                    widget: this,
                })));
            this.$('.oe_fileupload').show();
            this.$('.o_image[data-mimetype^="image"]').each(function() {
                var $img = $(this);
                if (/gif|jpe|jpg|png/.test($img.data('mimetype')) && $img.data('src')) {
                    $img.css('background-image', "url('" + $img.data('src') + "')");
                }
            });
        },
        /**
         * Handles the click event on the attachment button.
         */
        _onAttach: function() {
            this.$('.o_input_file').click();
        },

        /**
         * Handles the click event on the delete attachment button.
         */
        _onDelete: function(ev) {
            // Used to unlink the attachment
            ev.preventDefault();
            ev.stopPropagation();

            var fileID = $(ev.currentTarget).data('id');
            var record = _.findWhere(this.value.data, {
                res_id: fileID
            });
            if (record) {
                this._setValue({
                    operation: 'FORGET',
                    ids: [record.id],
                });
                var metadata = this.metadata[record.id];
                if (!metadata || metadata.allowUnlink) {
                    this._rpc({
                        model: 'ir.attachment',
                        method: 'unlink',
                        args: [record.res_id],
                    });
                }
            }
        },
        /**
         * Handles the change event on the file input field.
         */
        _onFileChanged: function(ev) {
            var self = this;
            ev.stopPropagation();

            var files = ev.target.files;
            var attachment_ids = this.value.res_ids;
            if (files.length === 0)
                return;

            _.each(files, function(file) {
                var record = _.find(self.value.data, function(attachment) {
                    return attachment.data.name === file.name;
                });
                if (record) {
                    var metadata = self.metadata[record.id];
                    if (!metadata || metadata.allowUnlink) {
                        attachment_ids = _.without(attachment_ids, record.res_id);
                        self._rpc({
                            model: 'ir.attachment',
                            method: 'unlink',
                            args: [record.res_id],
                        });
                    }
                }
                self.uploadingFiles.push(file);
            });

            this._setValue({
                operation: 'REPLACE_WITH',
                ids: attachment_ids,
            });

            this.$('form.o_form_binary_form').submit();
            this.$('.oe_fileupload').hide();
            ev.target.value = "";
        },
        /**
         * Handles the file loaded event.
         */
        _onFileLoaded: function() {
            var self = this;
            var files = Array.prototype.slice.call(arguments, 1);
            this.uploadingFiles = [];

            var attachment_ids = this.value.res_ids;
            _.each(files, function(file) {
                if (file.error) {
                    self.do_warn(_t('Uploading Error'), file.error);
                } else {
                    attachment_ids.push(file.id);
                    self.uploadedFiles[file.id] = true;
                }
            });

            this._setValue({
                operation: 'REPLACE_WITH',
                ids: attachment_ids,
            });
        },
        /**
         * Handles the click event on the PDF file.
         */
        _onFilePDF: function(ev) {
            var self = this;
            var recordId = $(ev.currentTarget).data('id');

            // Check if preview is already open for this attachment
            if (!this.previewOpen[recordId]) {
                this.previewOpen[recordId] = true; // Set flag to indicate preview is open

                var fieldId = self._getId(ev.currentTarget);

                // Append the preview HTML to the widget element
                self.$el.append(`
                    <div class="zPDF_iframe" data-record-id="${recordId}">
                        <div class="pdc_close btn btn-primary">close</div>&nbsp;&nbsp;&nbsp;
                        <div class="btn btn-primary"><a href="/web/content/${fieldId}?download=true" style="text-decoration: none; color: white">download</a></div><br>
                        <iframe class="zPDF" scrolling="no" id="main" name="main" frameborder="0" style="min-height:600px;width:900px;height:100%;" src="/web/content/${fieldId}"></iframe>
                    </div>
                `);
            }
        },
        /**
         * Handles the click event on the close button of the attachment preview.
         */
        _onClosePreview: function(ev) {
            var recordId = $(ev.currentTarget).closest('.zPDF_iframe').data('record-id');
            delete this.previewOpen[recordId]; // Remove flag for closed preview

            // Close the attachment preview
            $(ev.currentTarget).closest('.zPDF_iframe').remove();
        }
    });

    field_registry.add("many2many_preview", many2many_preview);
    return many2many_preview
});

