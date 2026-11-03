/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { WebClient } from '@web/webclient/webclient';
import {Sidebar} from "@personal_organiser/webclient/sidebar/sidebar";
patch(WebClient, {
    components: {
        ...WebClient.components,
        Sidebar,
    },
})
