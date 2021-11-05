/** @odoo-module **/

import { AppBar } from '@irie_backend_theme/components/app_side_bar/app_bar';
import { WebClient }  from '@web/webclient/webclient';
import { HomeMenu } from '@irie_backend_theme/components/home_menu/home_menu';

WebClient.components = {
    ...WebClient.components,
    AppBar,
    HomeMenu
};
