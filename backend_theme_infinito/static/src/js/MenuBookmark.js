/** @odoo-module **/
import { signal, Component, onMounted, onWillUnmount, proxy, xml } from "@odoo/owl";


import {session} from "@web/session";

export function useThemeDrag(ref, axis) {
    let stopDragging;
    const endDrag = () => stopDragging?.();
    const startDrag = (event) => {
        if (event.button !== 0) {
            return;
        }
        const element = ref();
        event.preventDefault();
        const startY = event.clientY;
        const startX = event.clientX;
        const startLeft = element.offsetLeft;
        const startTop = element.offsetTop;
        stopDragging?.();
        const originalDisplay = element.style.display;
        element.style.display = "flex";
        const move = (moveEvent) => {
            if (axis === 'y') {
                element.style.top = `${startTop + moveEvent.clientY - startY}px`;
            } else {
                element.style.left = `${startLeft + moveEvent.clientX - startX}px`;
            }
        };
        document.addEventListener("mousemove", move);
        document.addEventListener("mouseup", endDrag);
        stopDragging = () => {
            document.removeEventListener("mousemove", move);
            document.removeEventListener("mouseup", endDrag);
            element.style.display = originalDisplay;
        };
    };
    onMounted(() => ref().addEventListener("mousedown", startDrag));
    onWillUnmount(() => {
        stopDragging?.();
        ref()?.removeEventListener("mousedown", startDrag);
    });
}

export default class MenuBookmark extends Component {
    setup() {
        super.setup();
        this.bookmarkRef = signal.ref();
        this.state = proxy({
            menus: session.infinitoMenuBookmarks || []
        })
        useThemeDrag(this.bookmarkRef, 'y');
    }

    get menuBookmark() {
        return this.state.menus;
    }

}

MenuBookmark.template = xml`
        <div class="menu-bookmark" id="menuBookmark" t-ref="this.bookmarkRef">
            <div class="menu-wrapper">
                <span class="heading">Menus</span>
                <div class="bookmark-list">
                    <t t-foreach="this.menuBookmark" t-as="menu" t-key="menu_index">
                        <a t-attf-href="{{ menu.url }}" class="menu" t-att-data-index="menu_index">
                            <span class="small"><t t-out="menu.short_name"/></span>
                            <span class="full" t-att-data-index="menu_index"><t t-out="menu.name"/></span>
                        </a>
                    </t>
                </div>
            </div>
        </div>`
