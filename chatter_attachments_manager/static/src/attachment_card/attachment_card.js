/** @odoo-module */
import { AttachmentCard } from '@mail/components/attachment_card/attachment_card';
import { useService } from "@web/core/utils/hooks";
import { patch } from '@web/core/utils/patch';
import rpc from 'web.rpc';
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
const { useRef } = owl;

patch(AttachmentCard.prototype, 'chatter_attachments_manager_attachment_card', {
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    /**
     * @override
     */
     setup() {
       this.orm = useService("orm");
       this.preview = useRef('preview_modal')
       this._super.apply(this, arguments);
    },
    /**
     * Offline Preview of file type 'docx', 'xlsx' and 'pdf'
     */
    async onClickPreviewOffline(ev){
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        var type = $(ev.currentTarget).data("type")
        this.preview.el.querySelector('#FileHead').textContent = ev.target.name
        if(type === 'xlsx' || type === 'docx'){
        this.preview.el.style.display = "block";
        var preview = rpc.query({
                    model: 'ir.attachment',
                    method: 'decode_content',
                    args: [parseInt(ev.target.id),type],
                }).then(function (data) {
                    if (type === 'xlsx'){
                    $('.XlsxTable').append(data)
                    var frame = $(".dataframe").attr('id', 'MyTable');
                    }
                    else if(type === 'docx'){
                     for (let para = 0; para < data.length; para++) {
                        self.preview.el.querySelector('.MyDocs').append(data[para])
                      };
                    }
                });
        }
       else{
         this.props.record.onClickImage()
       }
    },
    /**
     Close preview window
   **/
    stopPreviewButton(ev){
        this.preview.el.style.display= "none";
        this.preview.el.querySelector('.MyDocs').textContent = " ";
        $('#MyTable').remove();
        this.preview.el.querySelector('#FileHead').textContent = " ";
    },
     /**
     * Records can be edited by altering the file name and adding tags.
     */
    async onClickEditRecord(ev){
     ev.preventDefault();
     var attachment_id = parseInt(ev.target.id);
     await this.env.services.action.doAction({
                name: this.env._t("Attachment"),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: attachment_id,
                res_model: 'ir.attachment',
                context: { create: false },
        }, {
            onClose: async () => {
               await location.reload();
            },
        });
        },
     /**
     * For generating Qr Code contain download link of attachment.
     */
    _onClickQrCode(ev){
    var self = this;
    rpc.query({
         model: 'ir.attachment',
         method: 'generate_qr_code',
         args: [parseInt(ev.target.id)],
            }).then(function (data){
            var act = self.env.services.action.doAction({
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'chatter_attachments_manager.attachment_qr_report_template',
                report_file: 'chatter_attachments_manager.attachment_qr_report_template',
                data: data,
                });
                console.log(act,'act')
            });
    },
});
