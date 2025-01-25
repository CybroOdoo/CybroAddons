/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";
import { AttachmentList } from "@mail/core/common/attachment_list";
import { ImageActions } from "@mail/core/common/attachment_list";
import { isEventHandled, markEventHandled } from "@web/core/utils/misc";
import { useService } from "@web/core/utils/hooks";


patch(AttachmentList.prototype, {
    /**
     * @override
     */
        setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    },
    /**
     Open window to edit image record
   **/
    async onClickEditImgRecord(ev, attachment){
        ev.stopPropagation();
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        await this.env.services.action.doAction({
                name: _t("Attachment"),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: attachment.id,
                res_model: 'ir.attachment',
                context: { create: false },
        }, {
            onClose: async () => {
               await location.reload();
            },
        });
        },

    onClickImage(ev) {
             if (isEventHandled(ev, 'onClickEditImgRecord')) {
                return;
            }
            if (isEventHandled(ev, 'onClickImageEdit')) {
                return;
            }
        this._super.apply(this, arguments);
    },

    /**
    Open a window to edit image
   **/
    async onClickImageEdit(ev, attachment) {
    var self = this;
    markEventHandled(ev, 'AttachmentImage.onClickImageEdit');

    // Initialize the image editor
    var imageEditor = new tui.ImageEditor('.tui-image-editor-container', {
        includeUI: {
            loadImage: {
                path: "/web/image/ir.attachment/" + attachment.id + "/datas",
                name: 'SampleImage'
            },
            imageSize: {
                oldWidth: "0",
                oldHeight: "0",
                newWidth: "300",
                newHeight: "90"
            },
            initMenu: 'filter',
            menuBarPosition: 'bottom'
        },
        cssMaxWidth: 500,
        cssMaxHeight: 590,
        usageStatistics: false
    });

    // Show the editor container
    const editorContainer = document.querySelector('#imageEditor');
    if (editorContainer) {
        editorContainer.style.display = 'block';
    }

    // Replace the download button with a save button
    const downloadButton = document.querySelector('.tui-image-editor-header-buttons .tui-image-editor-download-btn');
    if (downloadButton) {
        const saveButton = document.createElement('button');
        saveButton.classList.add('tui-image-editor-save-btn');
        saveButton.textContent = 'Save';
        downloadButton.replaceWith(saveButton);
    }

    // Add a close button to the header
    const headerButtons = document.querySelector('.tui-image-editor-header-buttons');
    if (headerButtons) {
        const closeButton = document.createElement('div');
        closeButton.classList.add('tui-image-editor-close-btn');
        closeButton.textContent = 'Close';
        closeButton.style.cssText = `
            background-color: #fff;
            border: 1px solid #ddd;
            color: #222;
            font-family: sans-serif;
            font-size: 12px;
            padding: 5px;
            cursor: pointer;
        `;
        headerButtons.appendChild(closeButton);

        // Add event listener for the close button
        closeButton.addEventListener('click', this.CloseImageEditor.bind(this));
    }

    // Add event listener for the save button
    const saveButton = document.querySelector('.tui-image-editor-save-btn');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            const myImage = imageEditor.toDataURL();
            const attachment_id = attachment.id;
            try {
                await self.orm.call("ir.attachment", "save_edited_image", [attachment_id, myImage]);
                location.reload(); // Reload the page after saving
            } catch (error) {
                console.error("Error saving edited image:", error);
            }
        });
    }
},

    CloseImageEditor: function(){
    var edit = jQuery.noConflict();
    edit('#imageEditor').css("display","none");
    },

    /**
     * Records can be edited by altering the file name and adding tags.
     */
    async onClickEditRecord(ev, attachment){
     ev.stopPropagation();
     ev.preventDefault();
     await this.env.services.action.doAction({
                name: _t("Attachment"),
                type: 'ir.actions.act_window',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: attachment.id,
                res_model: 'ir.attachment',
                context: { create: false },
        }, {
            onClose: async () => {
               await location.reload();
            },
        });
        },

   /**
    * Offline Preview of file type 'docx', 'xlsx' and 'pdf'
   */
    async onClickPreviewOffline(ev, attachment){
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        var type = $(ev.currentTarget).data("type")
        var modal = $('#xlsx_preview')[0]
        modal.querySelector('#FileHead').textContent = ev.target.name
       if (type === 'xls' || type === 'xlsx' || type === 'docx') {
          modal.style.display = "block";
         var preview = await this.orm.call
        ("ir.attachment", "decode_content", [parseInt(ev.target.id),type]).then(function (data) {
          if (type === 'xls' || type === 'xlsx'){
                    $('.MyDocs').empty();
                    $('.XlsxTable').append(data)
                    var frame = $(".dataframe").attr('id', 'MyTable');
                    }
          else if(type === 'docx'){
            $('.MyDocs').empty();
            for (let para = 0; para < data.length; para++) {
            $('.MyDocs').append(data[para])
            };
           }
                });
        }
       else{
         self.fileViewer.open(attachment, self.props.attachments)
       }
    },

       /**
     Close preview window
   **/
    stopPreviewButton(ev){
        ev.stopPropagation();
        ev.preventDefault();
        var modal = $('#xlsx_preview')[0]
        modal.style.display = "none";
    },

     /**
     * For generating Qr Code contain download link of attachment.
     */
    async _onClickQrCode(ev){
    ev.stopPropagation();
    ev.preventDefault();
    var self = this;
     await this.orm.call
        ("ir.attachment", "generate_qr_code", [parseInt(ev.target.id)]).then(function (data){
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
