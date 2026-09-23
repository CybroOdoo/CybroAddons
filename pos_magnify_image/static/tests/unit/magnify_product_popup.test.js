/** @odoo-module **/

import { expect, test } from "@odoo/hoot";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";

function makePopup() {
    const popup = Object.create(MagnifyProductPopup.prototype);
    popup.imageRef = { el: document.createElement("img") };
    popup.zoomLevel = 1;
    popup.isPanning = false;
    popup.startX = 0;
    popup.startY = 0;
    popup.translateX = 0;
    popup.translateY = 0;
    return popup;
}

test("the product image zoom is limited and resets its position at normal scale", () => {
    const popup = makePopup();
    let prevented = false;

    popup.onZoom({
        deltaY: -1,
        preventDefault: () => (prevented = true),
    });

    expect(prevented).toBe(true);
    expect(popup.zoomLevel).toBe(1.1);

    for (let index = 0; index < 30; index++) {
        popup.onZoom({ deltaY: -1, preventDefault: () => {} });
    }
    expect(popup.zoomLevel).toBe(3);

    popup.translateX = 25;
    popup.translateY = -15;
    for (let index = 0; index < 30; index++) {
        popup.onZoom({ deltaY: 1, preventDefault: () => {} });
    }

    expect(popup.zoomLevel).toBe(1);
    expect(popup.translateX).toBe(0);
    expect(popup.translateY).toBe(0);
});

test("the product image pans only while it is zoomed", () => {
    const popup = makePopup();

    popup.startPan({ clientX: 100, clientY: 50 });
    expect(popup.isPanning).toBe(false);

    popup.zoomLevel = 2;
    popup.startPan({ clientX: 100, clientY: 50 });
    popup.onPan({ clientX: 130, clientY: 70 });

    expect(popup.isPanning).toBe(true);
    expect(popup.translateX).toBe(30);
    expect(popup.translateY).toBe(20);
    expect(popup.imageRef.el.style.cursor).toBe("grabbing");

    popup.stopPan();
    expect(popup.isPanning).toBe(false);
    expect(popup.imageRef.el.style.cursor).toBe("grab");
});
