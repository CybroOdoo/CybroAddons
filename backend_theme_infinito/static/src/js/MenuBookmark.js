/** @odoo-module alias=backend_theme_infinito.MenuBookmark **/
// Import necessary components from Odoo Owl framework
const { Component, useState, xml, onMounted } = owl;
// Import session object from web session module
import { session } from "@web/session";

// Define a method for dragging elements
Component.prototype.dragElement = (elmnt, pos, display=true) => {
    // Initialize position variables
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    // Function to handle mouse down event for dragging
    elmnt.onmousedown = dragMouseDown;
    function dragMouseDown(e) {
      // Set display property of the element to 'flex'
      elmnt.style.display = 'flex';
      // Get the mouse position when the mouse button is pressed
      e = e || window.event;
      e.preventDefault();
      pos3 = e.clientX;
      pos4 = e.clientY;
      // Assign event handlers for mouse up and move events
      document.onmouseup = closeDragElement;
      document.onmousemove = elementDrag;
    }
    function elementDrag(e) {
      // Function to handle element dragging
      e = e || window.event;
      e.preventDefault();
      pos1 = pos3 - e.clientX;
      pos2 = pos4 - e.clientY;
      pos3 = e.clientX;
      pos4 = e.clientY;
      if(pos.includes('y')){
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
      }
      if(pos.includes('x')){
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
      }
    }
    function closeDragElement() {
      // Function to handle mouse up event and reset event handlers
      document.onmouseup = null;
      document.onmousemove = null;
      // Set display property of the element to 'none' if display is false
      if(!display){
        elmnt.style.display = 'none';
      }
    }
}
// Define the MenuBookmark component
export default class MenuBookmark extends Component {
    constructor(parent){
         // Constructor function for MenuBookmark component
        super(...arguments);
        this.parent = parent;
    }
    setup(){
        // Setup method to initialize component state and mount event
        super.setup();
        // Initialize component state with menu bookmarks from session
        this.state = useState({
            menus: session.infinitoMenuBookmarks
        })
        // Call the mounted method when the component is mounted
        onMounted(this.mounted);
    }
    get menuBookmark() {
        // Getter function to access the menu bookmarks from the component state
        return this.state.menus;
    }
    mounted(){
        // Method called when the component is mounted to enable dragging
        this.dragElement(this.__owl__.refs.menuBookmark, 'y', false);
    }
}

// Define the template for the MenuBookmark component
MenuBookmark.template = xml`
        <div class="menu-bookmark" id="menuBookmark" t-ref="menuBookmark">
            <div class="menu-wrapper">
                <span class="heading">Menus</span>
                <t t-foreach="menuBookmark" t-as="menu" t-key="menu_index">
                    <a t-attf-href="/{{ menu.url }}" class="menu" t-att-data-index="menu_index">
                        <span class="small"><t t-esc="menu.short_name"/></span>
                        <span class="full" t-att-data-index="menu_index"><t t-esc="menu.name"/></span>
                    </a>
                </t>
            </div>
        </div>`