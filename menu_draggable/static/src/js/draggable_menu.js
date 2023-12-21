/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import session from "web.session";
import rpc from 'web.rpc';
const { onWillStart, onMounted } = owl;
// Patch the navbar to drag and change the positions of menus in each model
patch(NavBar.prototype, 'menu_draggable/static/src/js/draggable_menu.js', {
    setup(){
        this._super.apply();
        onMounted(this.mount);
        onWillStart(this.willStart);
    },
    async willStart(){
    $(".ui-sortable-handle").attr('style', 'cursor:all-scroll;');
    },
    mount(){
        document.addEventListener('mousedown', this._dragMenu);
    },
    _dragMenu:async function(ev){
    $(".ui-sortable-handle").attr('style', 'cursor:all-scroll;');
        var menuItems = [] ;
        var selected_menu_data = $(".o_menu_sections")
        selected_menu_data.children().each(element => {
            menuItems.push($(selected_menu_data.children()[element]).text())
        })
        $(".o_menu_sections").sortable(
        );
        await rpc.query({
              model: 'menu.item.draggable',
              method: 'get_menu_item',
              args: [$(ev.target).data('section'), menuItems],
         }).then(function(response){})
    },
})
