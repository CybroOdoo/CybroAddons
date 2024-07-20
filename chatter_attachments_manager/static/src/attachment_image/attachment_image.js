/** @odoo-module **/
import { AttachmentImage } from '@mail/components/attachment_image/attachment_image';
import { patch } from 'web.utils';
import { isEventHandled, markEventHandled } from '@mail/utils/utils';
import rpc from 'web.rpc';
const { useRef,onWillUnmount,onMounted , useState} = owl.hooks;
const core = require('web.core');
const _t = core._t;
var dialogs = require('web.view_dialogs');

patch(AttachmentImage.prototype, 'chatter_attachments_manager/static/src/attachment_image/attachment_image.js', {
    setup() {
        this._super.apply(...arguments);
        this.image_menu = useRef('image_menu_dropdown');
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
    //------To close the dropdown on outside click
        if(this.state?.isDropdownOpen && !this.image_menu.el.contains(ev.target)){
            this.state.isDropdownOpen = false
        }
    },

    onClickImage(ev) {
    //----Handle click event on the settings button.Show or hide the context menu dropdown.
        ev.preventDefault();
        this.state.isDropdownOpen = !this.state.isDropdownOpen
        },

    onClickEditImgRecord(ev) {
    //----Open window to edit image record
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        const attachment_id = parseInt(ev.target.id);
        const action = {
            type: 'ir.actions.act_window',
            name: this.env._t("Edit Record"),
            res_model: 'ir.attachment',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment_id,
        };
        return this.env.bus.trigger('do-action', {
            action,
            options: {
                on_close: () => {},
            },
        });
    },

    async onClickImageEdit(ev) {
    //----Open a window to edit image
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickImageEdit');
        const attachment_id = parseInt(ev.target.id);
        const imageEditor = new tui.ImageEditor('.tui-image-editor-container', {
            includeUI: {
                loadImage: {
                    path: `/web/image/ir.attachment/${attachment_id}/datas`,
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

        $('#imageEditor').css("display", "block");
        $('.tui-image-editor-header-buttons .tui-image-editor-download-btn')
            .replaceWith(`<button class="tui-image-editor-save-btn">Save</button>`);
        $('.tui-image-editor-header-buttons').append(`
            <div class="tui-image-editor-close-btn"
                 style="background-color: #fff; border: 1px solid #ddd; color: #222; font-family: sans-serif; font-size: 12px">
                 Close
            </div>
        `);
        $('.tui-image-editor-header-buttons .tui-image-editor-close-btn')
            .on('click', () => {
                $('#imageEditor').css("display", "none");
            });

        $('.tui-image-editor-header-buttons .tui-image-editor-save-btn').on('click', () => {
            const myImage = imageEditor.toDataURL();
            rpc.query({
                model: 'ir.attachment',
                method: 'save_edited_image',
                args: [attachment_id, myImage],
            }).then(() => {
                location.reload();
            });
        });
    },
});
