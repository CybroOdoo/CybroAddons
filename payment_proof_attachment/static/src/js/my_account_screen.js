/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.MyAccountPaymentProof = publicWidget.Widget.extend({
    selector: '.my_account_screen',
    events: {
        'click #btnShowModal': '_onClickShowModal',
        'click .close_modal': '_onClickCloseModal',
        'change #my_account_payment_proof': '_onChangePaymentProof',
        'click #payment_proof_update': '_onClickUpdateAttachment',
        'click #btnShowReceipt': '_onClickShowReceipt',
        'click #refresh_receipt': '_onClickShowReceipt',
    },

    /**
     * for showing the modal dialog
     */
    _onClickShowModal: function () {
        const modal = this.el.querySelector('#myAccountModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    /**
     * for closing the modal dialog
     */
    _onClickCloseModal: function () {
        const modal = this.el.querySelector('#myAccountModal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    /**
     * getting content from the uploaded file
     */
    _onChangePaymentProof: function (ev) {
        const files = ev.target.files;
        var fileList = [];
        var filesProcessed = 0;

        for (let i = 0; i < files.length; i++) {
            var reader = new FileReader();
            reader.onload = (function(file) {
                return function(e) {
                    var dataURL = e.target.result.split(',')[1];
                    fileList.push({
                        name: file.name,
                        content: dataURL
                    });
                    filesProcessed++;
                };
            })(files[i]);
            reader.readAsDataURL(files[i]);
        }
        this.fileList = fileList;
    },

    /**
     * transfer the content to python in my account screen
     */
    _onClickUpdateAttachment: function (ev) {
        var self = this;
        const modal = this.el.querySelector('#myAccountModal');

        if (modal) {
            modal.style.display = 'none';
        }

        if (self.fileList && self.fileList.length > 0) {
            var saleId = ev.currentTarget.getAttribute('value');

            rpc('/payment_proof/submit', {
                'sale_id': Number(saleId),
                'attachments': this.fileList
            }).then(function () {
                self.fileList = [];
                var fileInput = self.el.querySelector("#my_account_payment_proof");
                if (fileInput) {
                    fileInput.value = "";
                }
                // Optionally refresh the receipt list
                self._onClickShowReceipt();
            });
        }
    },

    /**
     * getting updated attachments
     */
    _onClickShowReceipt: function (ev) {
        var self = this;
        const receiptDiv = this.el.querySelector('#updated_receipt');
        const btnShowReceipt = this.el.querySelector('#btnShowReceipt');

        if (receiptDiv) {
            receiptDiv.style.display = 'block';
        }
        if (btnShowReceipt) {
            btnShowReceipt.style.display = 'none';
        }

        var saleId = btnShowReceipt ? btnShowReceipt.getAttribute('value') : null;

        rpc('/my_account_screen/show_updated', {
            'data': saleId,
        }).then(function (attachment_ids) {
            var showingDiv = self.el.querySelector("#showing_updated_receipt");
            if (!showingDiv) return;

            showingDiv.innerHTML = '';

            if (attachment_ids && attachment_ids.length > 0) {
                attachment_ids.forEach(function(attachment) {
                    var id = "/web/content/" + attachment['id'];
                    var name = attachment['name'];
                    var link = document.createElement('a');
                    link.style.cssText = 'width:200px; margin-bottom: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display:inline-block;';
                    link.className = 'btn btn-outline-secondary';
                    link.href = id;
                    link.target = '_blank';
                    link.innerHTML = name + " <i class='fa fa-download'></i>";
                    showingDiv.appendChild(link);
                    showingDiv.appendChild(document.createElement('br'));
                });
            } else {
                var noAttachMsg = document.createElement('p');
                noAttachMsg.style.color = 'red';
                noAttachMsg.textContent = 'There are no attachments for this sale order.';
                showingDiv.appendChild(noAttachMsg);
            }
        });
    }
});