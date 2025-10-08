/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
// import to ensure mail Messaging patches are loaded beforehand

registerPatch({
    name: 'Attachment',
    recordMethods: {
        /**
         * @override onClickDownload(ev)
         */
         onClickDownload(ev) {
            ev.stopPropagation();
            window.open(this.defaultSource)
            this.download();
        },
    },
})
