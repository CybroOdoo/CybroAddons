/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PaymentProof = publicWidget.Widget.extend({
    init() {
        this.rpc = this.bindService("rpc");
    },
    selector: '.payment_screen',
    events: {
        'click #btnShowModal': '_onClickShowModal',
        'click .close_modal': '_onClickCloseModal',
        'change #payment_proof': '_onChangePaymentProof',
        'click #payment_proof_cart_update': '_onClickUpdateAttachment',
        'click #paymentScreenBtnShowReceipt': '_onClickShowReceipt',
        'click #refresh_payment_receipt': '_onClickShowReceipt',
    },
    /**
     *for closing the modal dialog
     */
    _onClickShowModal: function () {
        this.el.querySelector('#myModal').style.display = 'block';
    },
    /**
     *for closing the modal dialog
     */
    _onClickCloseModal: function () {
        this.el.querySelector('#myModal').style.display = 'none';
    },
    /**
     *getting content from the uploaded file
     */
    _onChangePaymentProof: function (ev) {
        const files = ev.target.files;
        var fileList = [];
        for (let i = 0; i < files.length; i++) {
            var reader = new FileReader();
            var reader_content = reader.readAsDataURL(files[i]);
            reader.onload = function (reader_content) {
                var dataURL = reader_content.target.result.split(',')[1];
                var fileName = files[i].name;
                fileList.push({
                    name: fileName,
                    content: dataURL
                });
            }
        }
        this.fileList = fileList;
    },
    /**
     *transfer the content to python in payment screen
     */
    _onClickUpdateAttachment: function (ev) {
        var self = this;
        this.el.querySelector('#myModal').style.display = 'none';
        if (self.fileList) {
            this.rpc('/payment_proof/submit', {
                'attachments': this.fileList
            }).then(function () {
                self.fileList = ""
                self.$el.find("#payment_proof").val("")
            });
        }
    },
    /**
     *getting updated attachments
     */
    _onClickShowReceipt: function () {
        var self = this;
        this.$el.find('#updated_receipt').css("display", "block")
        this.$el.find('#paymentScreenBtnShowReceipt').css("display", "none")
        this.rpc('/my_account_screen/show_updated', {}).then(function (attachment_ids) {
            if (attachment_ids.length > 0) {
                self.$el.find("#showing_updated_receipt").empty();
                $(attachment_ids).each(function (attachment_id) {
                    var id = "/web/content/" + attachment_ids[attachment_id]['id']
                    var name = attachment_ids[attachment_id]['name']
                    self.$el.find('#showing_updated_receipt').append("<a class='btn btn-outline-info' href='" + id + "'>" + name + " <i class='fa fa-download'></i></a><br/>");
                });
            } else {
                self.$el.find("#showing_updated_receipt").empty();
                self.$el.find('#showing_updated_receipt').append("<p style='color:yellow;>There is no attachments for this sale order.</p>")
            }
        })
    }
})
