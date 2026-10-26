import { expect, test } from "@odoo/hoot";
import { contains, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { ScaleScreen } from "@pos_weight_manual/js/scale_screen";

definePosModels();

test("ScaleScreen renders correctly with product details and unit price", async () => {
    await setupPosEnv();

    await mountWithCleanup(ScaleScreen, {
        props: {
            productName: "Fresh Apples",
            uomName: "kg",
            uomRounding: 0.01,
            productPrice: 5.0,
            close: () => {},
            getPayload: () => {},
        },
    });

    expect(".modal-title").toHaveText("Fresh Apples");
    expect("label").toHaveText("Weight:");
    expect("input[type='number']").toHaveCount(1);
    expect("span.ms-2").toHaveText("kg");
});

test("ScaleScreen computes price on manual weight input and confirms payload", async () => {
    await setupPosEnv();

    let confirmedWeight = null;
    let closed = false;

    const component = await mountWithCleanup(ScaleScreen, {
        props: {
            productName: "Fresh Oranges",
            uomName: "kg",
            uomRounding: 0.01,
            productPrice: 4.0,
            close: () => {
                closed = true;
            },
            getPayload: (weight) => {
                confirmedWeight = weight;
            },
        },
    });

    await contains("input[type='number']").edit("2.5", { instantly: true });
    expect(component.state.weight).toBe(2.5);
    expect(component.netWeight).toBe(2.5);

    await contains("button.btn-primary").click();

    expect(confirmedWeight).toBe(2.5);
    expect(closed).toBe(true);
});

test("Closing ScaleScreen triggers close without submitting weight", async () => {
    await setupPosEnv();

    let submitted = false;
    let closed = false;

    await mountWithCleanup(ScaleScreen, {
        props: {
            productName: "Watermelon",
            uomName: "kg",
            uomRounding: 0.01,
            productPrice: 3.0,
            close: () => {
                closed = true;
            },
            getPayload: () => {
                submitted = true;
            },
        },
    });

    await contains("button.btn-close").click();

    expect(closed).toBe(true);
    expect(submitted).toBe(false);
});
