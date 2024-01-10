/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu"
const { onMounted, onWillUnmount } = owl;
var rpc = require('web.rpc');

patch(HomeMenu.prototype, "menu_item_draggable.draggable_menu", {
    /*HomeMenu is patched and extended to write draggable functions.*/
    setup() {
        this._super.apply();
        onMounted(this.mount);
    },
    mount() {
        document.addEventListener('mousedown', this._mousedown);
        document.addEventListener('mouseup', this._mouseup);
    },
    _mousedown: async function (ev) {
        /*on mousedown the home menu list is taken and passed.*/
        var homeMenuItems = [];
        var menuItems = [];
        var sortable_menu = $(".o_apps").sortable()
        sortable_menu.children().each(element => {
            homeMenuItems.push($(sortable_menu.children()[element]).text())
            menuItems.push($(sortable_menu.children()[element])[0].hash.match(/menu_id=(\d+)/)[1])
        })
        $(".o_apps").sortable();
        try {
            var menu_id = (ev.target.parentElement.attributes[5].nodeValue).split('&')[0].split('=')[1]
            await rpc.query({
                model: 'draggable.home.menu.item',
                method: 'get_home_menu_item',
                args: [menu_id, homeMenuItems, menuItems],
            }).then(function (response) { })
        }
        catch (e) {
        }
    },
    _mouseup: async function (ev) {
        /*on mouseup the home menu list is taken and passed.
        Also if the return response is False then current window is reloaded.*/
        var self = this;
        var homeMenuItems = [];
        var menu_dict = {}
        var menuItems = [];
        var sortable_menu = $(".o_apps").sortable();
        sortable_menu.children().each(element => {
            homeMenuItems.push($(sortable_menu.children()[element]).text())
            menuItems.push($(sortable_menu.children()[element])[0].hash.match(/menu_id=(\d+)/)[1])
        })
        $(".o_apps").sortable();
        try {
            var menu_id = (ev.target.parentElement.attributes[5].nodeValue).split('&')[0].split('=')[1]
            await rpc.query({
                model: 'draggable.home.menu.item',
                method: 'get_home_menu_item',
                args: [menu_id, homeMenuItems, menuItems],
            }).then(function (response) {
                if (response.type === 'False') {
                    window.location.reload();
                }
            })
        }
        catch (e) {
        }
    },
});