/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { rpc } from "@web/core/network/rpc";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from '@web/core/l10n/translation';

patch(ListController.prototype, {
    //    /**
    //     * Handle the click event for upload documents.
    //     */
    _onClickAttachment: async function() {
        var self = this;
        const SelectedRecords = await self.model.root.getResIds(true);
        var OnSelectedDocument = function(e) {
            var result_doc = []
            for (var i = 0; i < this.files.length; i++) {
                (function(file) {
                    var reader = new FileReader();
                    reader.onloadend = function(e) {
                        var dataurl = e.target.result;
                        rpc('/web/dataset/call_kw/upload.multi.documents/document_file_create', {
                            model: 'upload.multi.documents',
                            method: 'document_file_create',
                            args: [dataurl, file.name, SelectedRecords, self.props.resModel],
                            kwargs: {},
                        }).then(function(result) {
                            if (result) {
                                result_doc.push(result)
                            }
                        });
                    }
                    reader.readAsDataURL(file);
                })(this.files[i]);
            }
            if (result_doc) {
                self.dialogService.add(AlertDialog, {
                    title: _t('Succeeded !!'),
                    body: _t("Updated successfully."),
                    confirmLabel: _t('Ok'),
                });
            } else {
                self.dialogService.add(AlertDialog, {
                    title: _t('Failed !!'),
                    body: _t("Please select record."),
                    confirmLabel: _t('Ok'),
                });
            }
        };
        var UploadFileDocument = document.createElement('input');
        UploadFileDocument.setAttribute('type', 'file');
        UploadFileDocument.setAttribute('multiple', 'multiple');
        UploadFileDocument.click();
        UploadFileDocument.addEventListener('change', OnSelectedDocument);
    }
})
