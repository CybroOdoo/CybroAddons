/** @odoo-module **/
import {BlockUI} from "@web/core/ui/block_ui";
import {ImportBlockUI} from "@base_import/import_block_ui";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";



patch(BlockUI.prototype, {
    setup() {
        super.setup();
        this.loaderClass = session.loaderClass;
    },
});
patch(ImportBlockUI.prototype, {
    setup() {
        super.setup();
        this.loaderClass = session.loaderClass;
    },
});

