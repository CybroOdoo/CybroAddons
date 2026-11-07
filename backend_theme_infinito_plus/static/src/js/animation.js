/** @odoo-module **/
import { session } from "@web/session";

const ANIMATION_CLASSES = {
    "Scale": "infinito-anim-scale",
    "Slide in": "infinito-anim-slide-in",
};

export function applyAnimation(name) {
    const root = document.documentElement;
    root.classList.remove(...Object.values(ANIMATION_CLASSES));
    if (ANIMATION_CLASSES[name]) {
        root.classList.add(ANIMATION_CLASSES[name]);
    }
}

applyAnimation(session.infinitoAnimation);