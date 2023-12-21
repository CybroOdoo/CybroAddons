/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu"
var rpc = require('web.rpc');
// Patch the HomeMenu prototype to add draggable_menu functionality
patch(HomeMenu.prototype, "menu_item_draggable.draggable_menu", {
    // Call the original setup method and add onMounted hook
    setup() {
        this._super.apply();
    },
    /**
     * Toggle the active class for the clicked category.
     */
    _active: async function(ev) {
        if (ev.currentTarget.closest('.apps-sortable-div')) {
            const currentActiveDiv = ev.currentTarget.closest('.apps-sortable-div');
            const allDivs = currentActiveDiv.parentElement.querySelectorAll('.apps-sortable-div');
            allDivs.forEach(div => {
                if (div !== currentActiveDiv) {
                    div.classList.remove('active-category');
                }
            });
        currentActiveDiv.classList.add('active-category');
        }
    },
    /**
     * Handle the drag start event.
     */
    dragStart: async function(e) {
        e.dataTransfer.setData('Menu_id', e.target.id)
        e.dataTransfer.effectAllowed = 'move';
        e.target.classList.add('beginDrag');
    },
    /**
     * Handle the dropped event after dragging.
     */
    dropped: async function(e) {
        // get new and old index
        var dragged_menu = e.dataTransfer.getData('Menu_id')
        var previousElement = e.dataTransfer.getData('Element')
        var dropped_menu = e.target.id
        var categoryName = e.target.attributes[1].nodeValue
        if (dragged_menu && dropped_menu) {
            e.target.classList.add('bye')
            await rpc.query({
                model: 'ir.app.category',
                method: 'apps_switching',
                args: [dragged_menu, dropped_menu]
            }).then(function() {
                window.location.reload()
            })
        } else if (dragged_menu && categoryName) {
            await rpc.query({
                model: 'ir.app.category',
                method: 'category_change',
                args: [dragged_menu, categoryName]
            }).then(function() {
                window.location.reload()
            })
        }
    },
    /**
     * Prevent the default behavior of the event.
     */
    cancelDefault: async function(e) {
        e.preventDefault()
        e.stopPropagation()
        return false
    },
});
