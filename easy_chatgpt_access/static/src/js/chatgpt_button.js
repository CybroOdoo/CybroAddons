/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { Wysiwyg } from "@html_editor/wysiwyg";
import { QWebPlugin } from "@html_editor/others/qweb_plugin";

export class SystrayIcon extends Component {
    static components = { Wysiwyg }
    setup() {
        this.state = useState({
            open: false,
        })
        onWillStart(async () => await this._lazyloadWysiwyg())
    };

    async _lazyloadWysiwyg() {
        // In Odoo 19, we don't need manual bundle loading if we depend on html_editor
        this.Wysiwyg = Wysiwyg;
    }

    get wysiwygProps() {
        return {
            onLoad: this.startWysiwyg.bind(this),
            config: this.wysiwygConfig
        }
    }

    get wysiwygConfig() {
        return {
            openPrompt: this.state.open,
            systray: {
                insert: false,
            }
        }
    }

    async startWysiwyg(editor) {
        this.editor = editor;
        this.isRendered = true;
    }

    _onClick() {
        this.state.open = !this.state.open
        setTimeout(() => {
            this.state.open = false;
        }, 500);
    };
};

SystrayIcon.template = "systray_icon";
export const systrayItem = {
    Component: SystrayIcon,
};
registry.category("systray").add("SystrayIcon", systrayItem);
