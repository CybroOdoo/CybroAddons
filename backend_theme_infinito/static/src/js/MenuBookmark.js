import { signal } from "@odoo/owl";
import { Component, onMounted, proxy, xml } from "@odoo/owl";
/** @odoo-module alias=backend_theme_infinito.MenuBookmark **/

import {session} from "@web/session";

Component.prototype.dragElement = (elmnt, pos, display = true) => {
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        elmnt.style.display = 'flex';
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        if (pos.includes('y')) {
            elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        }
        if (pos.includes('x')) {
            elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
        }
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
        if (!display) {
            elmnt.style.display = 'none';
        }
    }
}
export default class MenuBookmark extends Component {
    constructor(parent) {
        super(...arguments);
        this.parent = parent;
    }

    setup() {
        super.setup();
        this.bookmarkRef = signal.ref();
        this.state = proxy({
            menus: session.infinitoMenuBookmarks
        })
        onMounted(this.mounted);
    }

    get menuBookmark() {
        return this.state.menus;
    }

    mounted() {
        this.dragElement(this.bookmarkRef(), 'y', false);
    }
}

MenuBookmark.template = xml`
        <div class="menu-bookmark" id="menuBookmark" t-ref="this.bookmarkRef">
            <div class="menu-wrapper">
                <span class="heading">Menus</span>
                <div class="bookmark-list">
                    <t t-foreach="this.menuBookmark" t-as="menu" t-key="menu_index">
                        <a t-attf-href="{{ menu.url }}" class="menu" t-att-data-index="menu_index">
                            <span class="small"><t t-esc="menu.short_name"/></span>
                            <span class="full" t-att-data-index="menu_index"><t t-esc="menu.name"/></span>
                        </a>
                    </t>
                </div>
            </div>
        </div>`