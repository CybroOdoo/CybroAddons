/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.PaymentScreenProof = publicWidget.Widget.extend({
    selector: '.payment_screen',
    events: {
        'click #paymentScreenBtnShowModal': '_onClickShowModal',
        'click .close_payment_modal': '_onClickCloseModal',
        'change #payment_screen_payment_proof': '_onChangePaymentProof',
        'click #payment_proof_cart_update': '_onClickUpdateAttachment',
        'click #paymentScreenBtnShowReceipt': '_onClickShowReceipt',
        'click #refresh_payment_receipt': '_onClickShowReceipt',
    },

    /**
     * for showing the modal dialog
     */
    _onClickShowModal: function () {
        const modal = this.el.querySelector('#paymentScreenModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    /**
     * for closing the modal dialog
     */
    _onClickCloseModal: function () {
        const modal = this.el.querySelector('#paymentScreenModal');
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

        for (let i = 0; i < files.length; i++) {
            var reader = new FileReader();
            reader.onload = (function(file) {
                return function(e) {
                    var dataURL = e.target.result.split(',')[1];
                    fileList.push({
                        name: file.name,
                        content: dataURL
                    });
                };
            })(files[i]);
            reader.readAsDataURL(files[i]);
        }
        this.fileList = fileList;
    },

    /**
     * transfer the content to python in payment screen
     */
    _onClickUpdateAttachment: function (ev) {
        var self = this;
        const modal = this.el.querySelector('#paymentScreenModal');

        if (modal) {
            modal.style.display = 'none';
        }

        if (self.fileList && self.fileList.length > 0) {
            var saleOrderId = this._getSaleOrderId(ev);

            rpc('/payment_proof/submit', {
                'sale_id': saleOrderId,
                'attachments': this.fileList
            }).then(function () {
                self.fileList = [];
                var fileInput = self.el.querySelector("#payment_screen_payment_proof");
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
        const receiptDiv = this.el.querySelector('#payment_screen_updated_receipt');
        const btnShowReceipt = this.el.querySelector('#paymentScreenBtnShowReceipt');

        if (receiptDiv) {
            receiptDiv.style.display = 'block';
        }
        if (btnShowReceipt) {
            btnShowReceipt.style.display = 'none';
        }

        var saleOrderId = this._getSaleOrderId(ev);

        rpc('/my_account_screen/show_updated', {
            'data': String(saleOrderId)
        }).then(function (attachment_ids) {
            var showingDiv = self.el.querySelector("#payment_screen_showing_updated_receipt");
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
                noAttachMsg.style.color = 'orange';
                noAttachMsg.textContent = 'There are no attachments for this sale order.';
                showingDiv.appendChild(noAttachMsg);
            }
        });
    },

    /**
     * Helper method to get sale_order_id from multiple possible sources
     */
    _getSaleOrderId: function (ev) {
        var saleOrderId = null;

        // Try from event target
        if (ev && ev.currentTarget) {
            saleOrderId = ev.currentTarget.getAttribute('data-order-id') ||
                         ev.currentTarget.getAttribute('value');
        }

        // Try from show receipt button
        if (!saleOrderId) {
            var showReceiptBtn = this.el.querySelector('#paymentScreenBtnShowReceipt');
            if (showReceiptBtn) {
                saleOrderId = showReceiptBtn.getAttribute('data-order-id');
            }
        }

        // Try from save button
        if (!saleOrderId) {
            var saveBtn = this.el.querySelector('#payment_proof_cart_update');
            if (saveBtn) {
                saleOrderId = saveBtn.getAttribute('data-order-id');
            }
        }

        return saleOrderId ? Number(saleOrderId) : null;
    }
});