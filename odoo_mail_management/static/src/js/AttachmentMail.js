/** @odoo-module **/
import { Component, useRef} from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class ImportDialog extends Component {
    /**
     *handle the json file and import the data
     **/
    setup() {
        this.file = false
    }
    onChangeFileInput(ev) {
        const { files } = ev.target
        if (!files[0]) return;
        this.file = files[0]
    }
    async onFileUpload(ev) {    if (this.file){
        this.props.addAttachment(this.file)
        this.cancel()
        }
    }
    cancel() {
        this.props.close();
    }
}

ImportDialog.template = "ImportDialog"
ImportDialog.components = { Dialog }
