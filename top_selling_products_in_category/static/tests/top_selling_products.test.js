import { describe, expect, test } from "@odoo/hoot";
import { onRpc } from "@web/../tests/web_test_helpers";
import { setupInteractionWhiteList, startInteractions } from "@web/../tests/public/helpers";
import "@top_selling_products_in_category/js/top_selling_products";

setupInteractionWhiteList(["top_selling_products_in_category.top_selling_products"]);
describe.current.tags("interaction_dev");

describe("top_selling_products_in_category", () => {
    test("renders top selling products grouped by category into snippet", async () => {

        const fakeProducts = [
            {
                id: 1,
                name: "High Selling Product",
                public_categ_ids: [10],
                website_id: [1, "Website 1"],
                sales_count: 10,
            },
            {
                id: 2,
                name: "Medium Selling Product",
                public_categ_ids: [10],
                website_id: [1, "Website 1"],
                sales_count: 5,
            },
        ];
        const fakeCategories = [
            { id: 10, name: "Electronics", website_id: [1, "Website 1"] },
        ];

        onRpc("/top_products/categories", () => [fakeProducts, fakeCategories, 1]);

        await startInteractions(`
            <div class="products_category_wise_snippet">
                <div id="top_products_carousel"></div>
            </div>
        `);

        expect("#top_products_carousel .product_list").toHaveCount(1);
        expect("#top_products_carousel .product_list h2").toHaveText("Electronics");
        expect("#top_products_carousel .view-all-button").toHaveCount(1);
        expect("#top_products_carousel .card-title").toHaveCount(2);
    });

    test("handles multiple products and carousel slider creation", async () => {
        // 5 products in category 10 so it splits into 2 chunks and enables carousel
        const fakeProducts = [
            { id: 1, name: "Product 1", public_categ_ids: [10], sales_count: 20 },
            { id: 2, name: "Product 2", public_categ_ids: [10], sales_count: 15 },
            { id: 3, name: "Product 3", public_categ_ids: [10], sales_count: 10 },
            { id: 4, name: "Product 4", public_categ_ids: [10], sales_count: 8 },
            { id: 5, name: "Product 5", public_categ_ids: [10], sales_count: 5 },
        ];
        const fakeCategories = [
            { id: 10, name: "Gadgets", website_id: false },
        ];

        onRpc("/top_products/categories", () => [fakeProducts, fakeCategories, 1]);

        await startInteractions(`
            <div class="products_category_wise_snippet">
                <div id="top_products_carousel"></div>
            </div>
        `);

        expect("#top_products_carousel .carousel").toHaveCount(1);
        expect("#top_products_carousel .carousel-item").toHaveCount(2);
        expect("#top_products_carousel .carousel-control-prev").toHaveCount(1);
        expect("#top_products_carousel .carousel-control-next").toHaveCount(1);
    });

    test("handles empty response gracefully without errors", async () => {
        onRpc("/top_products/categories", () => [[], [], 1]);

        await startInteractions(`
            <div class="products_category_wise_snippet">
                <div id="top_products_carousel"></div>
            </div>
        `);

        expect("#top_products_carousel .product_list").toHaveCount(0);
    });
});
