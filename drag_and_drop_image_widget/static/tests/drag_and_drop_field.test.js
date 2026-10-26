/** @odoo-module */

import { describe, expect, test } from "@odoo/hoot";
import { click, queryFirst } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import {
    defineModels,
    fields,
    models,
    mountView,
} from "@web/../tests/web_test_helpers";

const SAMPLE_IMAGE_PNG =
    "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==";

class Partner extends models.Model {
    _name = "res.partner";

    name = fields.Char();
    avatar = fields.Binary();

    _records = [
        { id: 1, name: "Test Partner", avatar: SAMPLE_IMAGE_PNG },
        { id: 2, name: "Empty Partner", avatar: false },
    ];
}

defineModels([Partner]);

describe("drag_and_drop_image_widget", () => {
    describe.current.tags("desktop");

    test("DragAndDropBinaryField renders correctly with image and controls", async () => {
        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="avatar" widget="drag_and_drop"/>
                </form>
            `,
        });

        expect(".o_field_drag_and_drop").toHaveCount(1, {
            message: "The widget container should be rendered",
        });
        expect(".o_field_drag_and_drop img").toHaveCount(1, {
            message: "An image preview should be displayed",
        });
        expect(".o_select_file_button").toHaveCount(1, {
            message: "Edit button should be present",
        });
        expect(".o_clear_file_button").toHaveCount(1, {
            message: "Clear button should be present when image is set",
        });
        expect(".o_upload_image_button").toHaveCount(1, {
            message: "Upload/Drag trigger button should be present",
        });
        expect(".image_picker").toHaveClass("d-none", {
            message: "Image picker drawer should initially be hidden",
        });
    });

    test("clicking upload/drag button opens and closes the image picker", async () => {
        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="avatar" widget="drag_and_drop"/>
                </form>
            `,
        });

        // Click the trigger button
        await click(".o_field_drag_and_drop button[data-tooltip='Drag']");
        expect(".image_picker").not.toHaveClass("d-none", {
            message: "Image picker should be visible after clicking drag/upload button",
        });

        // Click the close button
        await click(".image_picker .btn-close");
        expect(".image_picker").toHaveClass("d-none", {
            message: "Image picker should be hidden after clicking close button",
        });
    });

    test("clearing image updates the field value", async () => {
        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="avatar" widget="drag_and_drop"/>
                </form>
            `,
        });

        expect(".o_clear_file_button").toHaveCount(1);
        await click(".o_clear_file_button");
        await animationFrame();
        expect(".o_clear_file_button").toHaveCount(0, {
            message: "Clear button should disappear once image is cleared",
        });
    });

    test("DragAndDropBinaryField supports zoom tooltip in readonly mode", async () => {
        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            mode: "readonly",
            arch: `
                <form>
                    <field name="avatar" widget="drag_and_drop" options="{'zoom': true}"/>
                </form>
            `,
        });

        const img = queryFirst(".o_field_drag_and_drop img");
        expect(img).toHaveAttribute("data-tooltip-template", "web.ImageZoomTooltip", {
            message: "Image should have the zoom tooltip template when zoom is enabled",
        });
    });
});
