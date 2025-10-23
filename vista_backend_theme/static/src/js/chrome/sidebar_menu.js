/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { useRef, onMounted } from "@odoo/owl";

patch(NavBar.prototype, {
    setup(){
        super.setup();
        this.closeSidebar = useRef("closeSidebars")
        this.openSidebar = useRef("openSidebar")
        this.sidebar = useRef("sidebar")
        this.sidebarPanel = useRef("sidebarPanel")
        this.closeSides = this.closeSide.bind(this)
        this.openSides = this.openSide.bind(this)

        onMounted(() => {
            const closeSide = this.closeSidebar.el
            const openSide = this.openSidebar.el
            if (closeSide){
                closeSide.addEventListener("click",this.closeSides)
            }
            if (openSide) {
                openSide.addEventListener("click",this.openSides)
            }
        });
    },

    closeSide(){
        this.openSidebar.el.style.display = 'block'
        this.closeSidebar.el.style.display = 'none'
        this.sidebarPanel.el.style.display = 'none';
        const nextElement = this.root.el.nextElementSibling;
        if (nextElement) {
            nextElement.style.marginLeft = '0px';
        }
        const top_heading = this.root.el.children[0].children[0].children[0];
        if(top_heading){
            top_heading.style.marginLeft = '0px';
        }
    },

    openSide(){
        this.closeSidebar.el.style.display = 'block'
        this.openSidebar.el.style.display = 'none'
        this.sidebarPanel.el.style.display = 'block';
        const nextElement = this.root.el.nextElementSibling;
        if (nextElement) {
            nextElement.style.marginLeft = '90px';
            nextElement.style.transition = 'all .1s linear';
        }
        const top_heading = this.root.el.children[0].children[0].children[0];
        if(top_heading){
            top_heading.style.marginLeft = '90px';
            top_heading.style.transition = 'all .1s linear';
        }
    }
})
