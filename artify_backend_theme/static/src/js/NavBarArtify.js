/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useRef,onMounted } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.SideBarPanel = useRef("sidebar_panel");
        this.openSidebar = useRef("openSidebar");
        this.closeSidebar = useRef("closeSidebar");
        this.topHeading = useRef("top_heading");
        onMounted(()=>{
            // Using querySelector to find the element with the class '.o_action_manager'.
          // This is a common approach when dealing with class-based selection.
          // Important: Ensure that the element with the class '.o_action_manager' exists in the DOM.
            this.actionManager = document.querySelector('.o_action_manager');
        })
    },

    // Method: onClickOpenMenu
    // Description: Handles the click event to open the menu.
    onClickOpenMenu(event){
        // Show necessary elements when opening the menu.
        this.closeSidebar.el.style.display = 'block'
        this.openSidebar.el.style.display = 'none'
        this.SideBarPanel.el.style.display = 'block'

        // Adjust styles for the action manager and top heading.
        this.actionManager.style.marginLeft = '200px';
        this.actionManager.style.transition = 'all 0.1s linear';


        this.topHeading.el.style.marginLeft = '200px';
        this.topHeading.el.style.transition = 'all 0.1s linear';
        this.topHeading.el.style.width = 'auto';
    },

    // Method: onClickCloseMenu
    // Description: Handles the click event to close the menu.
    onClickCloseMenu(event){
        // Show necessary elements when closing the menu
        this.openSidebar.el.style.display = 'block';
        this.closeSidebar.el.style.display = 'none';
        this.SideBarPanel.el.style.display = 'none';

        // Reset styles for the action manager and top heading.
        this.actionManager.style.marginLeft = '0px';
        this.actionManager.style.transition = 'all 0.1s linear';

        this.topHeading.el.style.marginLeft = '0px';
        this.topHeading.el.style.transition = 'all 0.1s linear';
        this.topHeading.el.style.width = 'auto';

    },

    // Method: onClickMenuItem
    // Description: Handles the click event for menu items.
    onClickMenuItem(ev){
        // Hide the sidebar panel and reset styles for the action manager and top heading.
        this.SideBarPanel.el.style.display = 'none';
        this.actionManager.style.marginLeft = '0px'
        this.topHeading.el.style.marginLeft = '0px';
        this.topHeading.el.style.transition = 'all .1s linear';
        this.topHeading.el.style.width = 'auto';
        this.closeSidebar.el.style.display = 'none';
        this.openSidebar.el.style.display = 'block';
    }
});
