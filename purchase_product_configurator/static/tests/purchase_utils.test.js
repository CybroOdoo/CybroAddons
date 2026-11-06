import { expect, test } from "@odoo/hoot";

import { getSelectedCustomPtav } from "../src/js/purchase_utils";

test("returns the selected custom attribute value", () => {
    const selected = { id: 2, is_custom: true };
    const ptal = {
        selected_attribute_value_ids: [1, 2],
        attribute_values: [
            { id: 1, is_custom: false },
            selected,
            { id: 3, is_custom: true },
        ],
    };

    expect(getSelectedCustomPtav(ptal)).toBe(selected);
});

test("returns undefined when there is no selected custom attribute value", () => {
    const ptal = {
        selected_attribute_value_ids: [1],
        attribute_values: [
            { id: 1, is_custom: false },
            { id: 2, is_custom: true },
        ],
    };

    expect(getSelectedCustomPtav(ptal)).toBe(undefined);
});
