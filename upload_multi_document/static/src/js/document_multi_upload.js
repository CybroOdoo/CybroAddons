odoo.define('upload_multi_document.upload', function(require) {
	"use strict";

	var ListController = require('web.ListController');
	var rpc = require('web.rpc');

	ListController.include({
		buttons_template: 'UploadDocumentList.Buttons',
		events: _.extend({}, ListController.prototype.events, {
			'click .on_upload_doc_list': '_onUploadList',
		}),
    // Function to upload multiple files
		_onUploadList: function() {
			var self = this;
			var OnSelectedDocument = function(e) {
				for (var i = 0; i < this.files.length; i++) {
					(function(file) {
						var reader = new FileReader();
						reader.onloadend = function(e) {
							var dataurl = e.target.result;
							rpc.query({
								model: 'upload.multi.documents',
								method: 'document_file_create',
								args: [dataurl, file.name, self.getSelectedIds(),self.modelName],
							}).then(function(result) {});
						}
						reader.readAsDataURL(file);
					})(this.files[i]);
				}
			};
			var UploadFileDocument = $('<input type="file" multiple="multiple">');
			UploadFileDocument.click();
			UploadFileDocument.on('change', OnSelectedDocument);
		},
	});
	return ListController
});