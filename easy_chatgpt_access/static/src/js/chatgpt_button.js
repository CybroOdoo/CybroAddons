/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import { QWebPlugin } from '@web_editor/js/backend/QWebPlugin';
let stripHistoryIds;

import { session } from "@web/session";


/* Export new class SystrayIcon by extending Component */
export class SystrayIcon extends Component {
    static components = { Wysiwyg }
    setup() {
        this.state = useState({
            open: false,
        })
        this.odoo_version = session.isEnterprise() ? 'Enterprise' : 'Community';
        onWillStart(async() => await this._lazyloadWysiwyg())
    };
    // Lazily loads the Wysiwyg module and its dependencies if not already loaded.
    async _lazyloadWysiwyg() {
        let wysiwygModule = await odoo.loader.modules.get('@web_editor/js/wysiwyg/wysiwyg');
        this.MoveNodePlugin = (await odoo.loader.modules.get('@web_editor/js/wysiwyg/MoveNodePlugin'))?.MoveNodePlugin;
        // Otherwise, load the module.
        if (!wysiwygModule) {
            await loadBundle('web_editor.backend_assets_wysiwyg');
            wysiwygModule = await odoo.loader.modules.get('@web_editor/js/wysiwyg/wysiwyg');
            this.MoveNodePlugin = (await odoo.loader.modules.get('@web_editor/js/wysiwyg/MoveNodePlugin')).MoveNodePlugin;
        }
        stripHistoryIds = wysiwygModule.stripHistoryIds;
        this.Wysiwyg = wysiwygModule.Wysiwyg;
    }
    /**
    * Retrieves Wysiwyg properties.
    * @returns {object} An object containing Wysiwyg properties.
    */
    get wysiwygProps() {
        return {
            startWysiwyg: this.startWysiwyg.bind(this),
            editingValue: undefined,
            options: this.wysiwygOptions
        }
    }
    // Include the 'open' parameter in the object to enable loading the prompt dialog from the Systray.
    get wysiwygOptions() {
        return {
            value: "",
            allowCommandVideo: false,
            autostart: false,
            collaborationChannel: undefined,
            editorPlugins: [QWebPlugin, this.MoveNodePlugin],
            field_id: "",
            height: undefined,
            inIframe: false,
            iframeCssAssets: undefined,
            iframeHtmlClass: undefined,
            linkOptions: {
                forceNewWindow: true,
            },
            maxHeight: undefined,
            mediaModalParams: {
                noVideos: true,
                useMediaLibrary: true,
            },
            minHeight: undefined,
            noAttachment: undefined,
            onDblClickEditableMedia: this._onDblClickEditableMedia.bind(this),
            onWysiwygBlur: this._onWysiwygBlur.bind(this),
            placeholder: "",
            resizable: false,
            snippets: undefined,
            tabsize: 0,
            document,
            openPrompt: this.state.open,
            systray: {
                insert: false,
            }
        }
    }
    _onDblClickEditableMedia(ev) {
        const el = ev.currentTarget;
        if (el.nodeName === 'IMG' && el.src) {
            this.wysiwyg.showImageFullscreen(el.src);
        }
    }
    _onWysiwygBlur() {
        // Avoid save on blur if the html field is in inline mode.
        if (!this.props.isInlineStyle) {
            this.commitChanges();
        }
    }
    async startWysiwyg(wysiwyg) {
        this.wysiwyg = wysiwyg;
        await this.wysiwyg.startEdition();
        wysiwyg.$editable[0].classList.add("odoo-editor-qweb");
        if (this.props.codeview) {
            const $codeviewButtonToolbar = $(`
                <div id="codeview-btn-group" class="btn-group">
                    <button class="o_codeview_btn btn btn-primary">
                        <i class="fa fa-code"></i>
                    </button>
                </div>
            `);
            this.wysiwyg.toolbarEl.append($codeviewButtonToolbar[0]);
            $codeviewButtonToolbar.click(this.toggleCodeView.bind(this));
        }
        this.wysiwyg.odooEditor.addEventListener("historyStep", () =>
            this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this._isDirty())
        );
        if (this.props.isCollaborative) {
            this.wysiwyg.odooEditor.addEventListener("onExternalHistorySteps", () =>
                this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this._isDirty())
            );
        }
        this.isRendered = true;
    }
    // Onclick event of systray Icon
    _onClick() {
        this.state.open = !this.state.open
        setTimeout(() => {
            this.state.open = false;
        }, 500);
    };
};
session.isEnterprise = function () {
            return !!session.server_version_info[5];
        };
SystrayIcon.template = "systray_icon";
export const systrayItem = {
    Component: SystrayIcon,
};
registry.category("systray").add("SystrayIcon", systrayItem);
