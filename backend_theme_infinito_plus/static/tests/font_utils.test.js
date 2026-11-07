/** @odoo-module **/
import { expect, test } from "@odoo/hoot";
import { getFontNameFromUrl } from "@backend_theme_infinito_plus/js/font_utils";

test("font name from a specimen URL", () => {
    expect(getFontNameFromUrl("https://fonts.google.com/specimen/Open+Sans")).toBe("Open Sans");
});

test("font name from a css2 URL", () => {
    expect(
        getFontNameFromUrl("https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap")
    ).toBe("Roboto");
});

test("no font name in an unrelated URL", () => {
    expect(getFontNameFromUrl("https://example.com")).toBe(null);
});