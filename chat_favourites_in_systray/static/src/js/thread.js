/** @odoo-module **/
import {
    registerClassPatchModel,
    registerFieldPatchModel,
} from '@mail/model/model_core';
import { attr } from '@mail/model/model_field';
import { insert, unlink } from '@mail/model/model_field_command';

registerClassPatchModel('mail.thread', 'chat_favourites_in_systray/static/src/js/thread.js', {

     //----------------------------------------------------------------------
    // Public
    //----------------------------------------------------------------------

    /**
     * @override
     */
    convertData(data) {
        const data2 = this._super(data);
         if ('is_favourite' in data) {
                data2.is_favourite = data.is_favourite;
                data2.model = 'mail.channel';
            }
        return data2;
    },

});

registerFieldPatchModel('mail.thread', 'chat_favourites_in_systray/static/src/js/thread.js', {

    is_favourite: attr(),
});
