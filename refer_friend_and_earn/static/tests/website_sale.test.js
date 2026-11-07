import { after, describe, expect, test } from "@odoo/hoot";
import { click } from "@odoo/hoot-dom";
import { setupInteractionWhiteList, startInteractions } from "@web/../tests/public/helpers";
import { registry } from "@web/core/registry";
import { ReferAndEarn } from "@refer_friend_and_earn/js/website_sale";

setupInteractionWhiteList("refer_friend_and_earn.refer_and_earn");

describe("refer_friend_and_earn > ReferAndEarn Interaction", () => {
    after(() => {
        setupInteractionWhiteList(null);
    });

    test("interaction is registered in public.interactions registry", () => {
        const registered = registry
            .category("public.interactions")
            .get("refer_friend_and_earn.refer_and_earn");
        expect(registered).toBe(ReferAndEarn);
        expect(ReferAndEarn.selector).toBe(".oe_website_sale, .o_cart_total, .wrap");
        const instance = new ReferAndEarn();
        expect(instance).toBeInstanceOf(ReferAndEarn);
    });

    test("_onClickShowPoints hides toggle link and reveals points form in parent element", async () => {
        await startInteractions(`
            <div class="o_cart_total wrap">
                <div class="cart-total-cell">
                    <a href="#" class="show_points btn btn-link p-0">I have points (50 pts)</a>
                    <div class="point_form d-none mt-2">
                        <input name="points" id="points" value="50"/>
                        <button id="points_apply">Apply</button>
                    </div>
                </div>
            </div>
        `);

        expect(".show_points").not.toHaveClass("d-none");
        expect(".point_form").toHaveClass("d-none");

        await click(".show_points");

        expect(".show_points").toHaveClass("d-none");
        expect(".point_form").not.toHaveClass("d-none");
    });

    test("_onClickShowPoints finds point_form in document when outside immediate parent", async () => {
        await startInteractions(`
            <div class="wrap">
                <div class="header-section">
                    <a href="#" class="show_points">I have points</a>
                </div>
                <div class="content-section">
                    <div class="point_form d-none">
                        <input name="points" value="20"/>
                    </div>
                </div>
            </div>
        `);

        expect(".show_points").not.toHaveClass("d-none");
        expect(".point_form").toHaveClass("d-none");

        await click(".show_points");

        expect(".show_points").toHaveClass("d-none");
        expect(".point_form").not.toHaveClass("d-none");
    });
});
