/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
import { isEventHandled, markEventHandled } from '@mail/utils/utils';
import rpc from 'web.rpc';

registerPatch({
    name: 'AttachmentImage',
    recordMethods: {
    /**
    on click image event
   **/
    onClickImage(ev) {
             if (isEventHandled(ev, 'AttachmentImage.onClickEditImgRecord')) {
                return;
            }
            if (isEventHandled(ev, 'AttachmentImage.onClickImageEdit')) {
                return;
            }
        this._super.apply(this, arguments);
    },
    /**
     Open window to edit image record
   **/
    async onClickEditImgRecord(ev){
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
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
    Open a window to edit image
   **/
    async onClickImageEdit(ev){
        markEventHandled(ev, 'AttachmentImage.onClickImageEdit');
        var attachment_id = parseInt(ev.target.id)
        var imageEditor = new tui.ImageEditor('.tui-image-editor-container', {
             includeUI: {
                 loadImage: {
                     path: "/web/image/ir.attachment/"+attachment_id+"/datas",
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
         $('#imageEditor').css("display","block");
         $('.tui-image-editor-header-buttons .tui-image-editor-download-btn').
            replaceWith('<button class="tui-image-editor-save-btn" >Save</button>')
         $('.tui-image-editor-header-buttons').append(`<div class="tui-image-editor-close-btn"
             style="background-color: #fff;border: 1px solid #ddd;color: #222;
             "font-family: sans-serif;font-size:= 12px">Close</div>`)
         $('.tui-image-editor-header-buttons .tui-image-editor-close-btn').
         on('click', this.CloseImageEditor)
         $('.tui-image-editor-header-buttons .tui-image-editor-save-btn').on('click', () => {
         const myImage = imageEditor.toDataURL();
         rpc.query({
             model: 'ir.attachment',
             method: 'save_edited_image',
             args: [attachment_id,myImage],
                }).then(function (data){
            location.reload();
            });
        });
        },
    CloseImageEditor: function(){
    var edit = jQuery.noConflict();
    edit('#imageEditor').css("display","none");
    },
    }
});
