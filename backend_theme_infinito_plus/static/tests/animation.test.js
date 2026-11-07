/** @odoo-module **/
import { expect, test } from "@odoo/hoot";
import { applyAnimation } from "@backend_theme_infinito_plus/js/animation";

const root = () => document.documentElement;

test("applyAnimation sets the class of the chosen animation only", () => {
    applyAnimation("Scale");
    expect(root().classList.contains("infinito-anim-scale")).toBe(true);
    applyAnimation("Slide in");
    expect(root().classList.contains("infinito-anim-scale")).toBe(false);
    expect(root().classList.contains("infinito-anim-slide-in")).toBe(true);
    applyAnimation("Default");
    expect(root().classList.contains("infinito-anim-slide-in")).toBe(false);
});