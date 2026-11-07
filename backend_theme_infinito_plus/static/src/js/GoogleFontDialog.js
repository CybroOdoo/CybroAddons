/** @odoo-module **/
import { Component, t, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Dialog used by the Plus sidebar to add a Google Font.
 * `save(url)` must resolve to false when the font could not be saved,
 * so the dialog stays open.
 */
export class GoogleFontDialog extends Component {
    static template = "backend_theme_infinito_plus.GoogleFontDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
        save: t.function(),
    });

    setup() {
        this.url = "";
        this.saving = false;
    }

    get title() {
        return _t("Add a Google Font");
    }

    onInput(ev) {
        this.url = ev.target.value;
    }

    async onSave() {
        if (this.saving) {
            return;
        }
        this.saving = true;
        try {
            await this.props.save(this.url);
        } finally {
            this.saving = false;
        }
    }
}