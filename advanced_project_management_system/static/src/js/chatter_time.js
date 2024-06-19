/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
import { attr, many, one } from '@mail/model/model_field';
import '@mail/models/messaging';
// Register a patch for the 'Message' model
registerPatch({
    name : 'Message',
    fields: {
        dateDay: {
            // Compute the 'dateDay' field
            compute() {
                 if (!this.date) {
                    return this.env._t("Today");
                }
                const date = this.date.format('YYYY-MM-DD');
                if (date === moment().format('YYYY-MM-DD')) {
                     return this.env._t("Today") + ' ' + moment(this.date).format('HH:mm:ss');
                } else if (
                    date === moment()
                        .subtract(1, 'days')
                        .format('YYYY-MM-DD')
                ) {
                    return this.env._t("Yesterday") + ' ' + moment(this.date).format('HH:mm:ss');
                }
                return this.date.format('MMMM D, YYYY HH:mm:ss');
            },
        },
    },
})
