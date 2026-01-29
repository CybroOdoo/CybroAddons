/** @odoo-module */
import { AttachmentCard } from '@mail/components/attachment_card/attachment_card';
import { isEventHandled, markEventHandled } from '@mail/utils/utils';
import { patch } from 'web.utils';
var rpc = require('web.rpc');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
const { useRef, useState, onMounted, onWillUnmount } = owl.hooks;
patch(AttachmentCard.prototype, 'chatter_attachments_manager/static/src/attachment_card/attachment_card.js', {
    setup() {
        this.preview = useRef('preview_modal')
        this._super.apply(this, arguments);
        this.control_menu = useRef('card_menu_dropdown');
        this._onClickGlobal = this._onClickGlobal.bind(this)
        this.state = useState({
            isDropdownOpen: false,
        });
        onMounted(() => {
        document.addEventListener('click', this._onClickGlobal)
        })
        onWillUnmount(() => {
        document.removeEventListener('click', this._onClickGlobal)
        })
     },
    _onClickGlobal(ev){
    //----To close the dropdown on outside click
        if(this.state?.isDropdownOpen && !this.control_menu.el.contains(ev.target)){
            this.state.isDropdownOpen = false
        }
    },
    onClickCard(){
    //---show the dropdown
        this.state.isDropdownOpen = !this.state.isDropdownOpen
    },

    async onClickPreviewOffline(ev){
    //----Offline Preview of file type 'docx', 'xlsx' and 'pdf'
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        var type = $(ev.currentTarget).data("type")
        var fileHeadElement = this.preview.el.querySelector('#FileHead');
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
            this.attachmentCard.onClickImage()
        }
    },

    stopPreviewButton(ev){
    //----Close preview window
        this.preview.el.style.display= "none";
        this.preview.el.querySelector('.MyDocs').textContent = " ";
        $('#MyTable').remove();
        this.preview.el.querySelector('#FileHead').textContent = " ";
    },

    async onClickEditRecord(ev) {
    //----Records can be edited by altering the file name and adding tags.
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentCard.onClickEditRecord');
        var attachment_id = parseInt(ev.target.id);
        const action = {
            name: this.env._t("Attachment"),
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment_id,
            res_model: 'ir.attachment',
        };
        return this.env.bus.trigger('do-action', {
            action,
            options: {},
        });
    },

    _onClickQrCode(ev){
    //----For generating Qr Code contain download link of attachment.
        var self = this;
        rpc.query({
             model: 'ir.attachment',
             method: 'generate_qr_code',
             args: [parseInt(ev.target.id)],
        }).then(function (data){
            const action = {
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'chatter_attachments_manager.attachment_qr_report_template',
                report_file: 'chatter_attachments_manager.attachment_qr_report_template',
                data: data,
        };
        return self.env.bus.trigger('do-action', {
            action,
            options: {
                on_close: async () => {
                    await location.reload();
                },
            },
        });
        var act = self.env.services.action.doAction({
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'chatter_attachments_manager.attachment_qr_report_template',
            report_file: 'chatter_attachments_manager.attachment_qr_report_template',
            data: data,
            });
        });
    },
});
