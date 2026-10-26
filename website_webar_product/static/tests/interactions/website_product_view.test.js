import { describe, expect, test } from "@odoo/hoot";
import { click, queryOne, tick } from "@odoo/hoot-dom";
import { onRpc } from "@web/../tests/web_test_helpers";
import { setupInteractionWhiteList, startInteractions } from "@web/../tests/public/helpers";
import { CarouselSlider } from "@website/interactions/carousel/carousel_slider";
import "@website_webar_product/js/website_product_view";

setupInteractionWhiteList(["website_webar_product.product_detail_view_3d"]);
describe.current.tags("interaction_dev");

const PRODUCT_PAGE_HTML = `
    <div class="o_wsale_product_page">
        <div class="o_carousel_product_outer">
            <div id="o-carousel-product" class="carousel slide">
                <div class="carousel-inner">
                    <div class="carousel-item active">
                        <img src="/web/image/product.template/1/image_1024" />
                    </div>
                </div>
            </div>
        </div>
        <div id="product_main" class="d-none" style="display: none;"></div>
        <div class="product_detail_img_footer">
            <div class="product_images active" data-type="image" data-bs-slide-to="0">
                <img src="/web/image/product.template/1/image_128" />
            </div>
            <div id="42" class="product_images" data-type="3d" data-bs-slide-to="1">
                <span>3D View</span>
            </div>
        </div>
    </div>
`;

test("Clicking 3D thumbnail fetches model data and creates model-viewer", async () => {
    onRpc("/product/ar_image", async (request) => {
        const { params } = await request.json();
        expect(params.product_id).toBe(42);
        return {
            type: "local",
            local_url: "/web/content/42/model.glb",
            ar_scale: "auto",
            ar_placement: "floor",
            auto_rotate: true,
        };
    });

    const { core } = await startInteractions(PRODUCT_PAGE_HTML);
    expect(core.interactions).toHaveLength(1);

    await click('.product_images[data-type="3d"]');
    await tick();

    const arThumb = queryOne('.product_images[data-type="3d"]');
    expect(arThumb.classList.contains("active")).toBe(true);

    const carouselOuter = queryOne(".o_carousel_product_outer");
    expect(carouselOuter.classList.contains("d-none")).toBe(true);

    const productMain = queryOne("#product_main");
    expect(productMain.classList.contains("d-none")).toBe(false);

    const modelViewer = queryOne("#model-viewer");
    expect(modelViewer).not.toBe(null);
    expect(modelViewer.getAttribute("src")).toBe("/web/content/42/model.glb");
    expect(modelViewer.hasAttribute("ar")).toBe(true);
    expect(modelViewer.getAttribute("ar-scale")).toBe("auto");
    expect(modelViewer.getAttribute("ar-placement")).toBe("floor");
    expect(modelViewer.hasAttribute("auto-rotate")).toBe(true);

    const arButton = queryOne("#custom-ar-button");
    expect(arButton).not.toBe(null);
    expect(arButton.textContent).toBe("View in AR");
});

test("Clicking regular thumbnail restores carousel and hides model viewer", async () => {
    onRpc("/product/ar_image", () => ({
        type: "local",
        local_url: "/web/content/42/model.glb",
    }));

    await startInteractions(PRODUCT_PAGE_HTML);

    await click('.product_images[data-type="3d"]');
    await tick();
    expect("#model-viewer").toHaveCount(1);

    await click('.product_images[data-type="image"]');
    await tick();

    const carouselOuter = queryOne(".o_carousel_product_outer");
    expect(carouselOuter.classList.contains("d-none")).toBe(false);

    const productMain = queryOne("#product_main");
    expect(productMain.classList.contains("d-none")).toBe(true);
    expect(productMain.children.length).toBe(0);

    const imgThumb = queryOne('.product_images[data-type="image"]');
    expect(imgThumb.classList.contains("active")).toBe(true);
});

test("URL-type AR model sets src to ar_url", async () => {
    onRpc("/product/ar_image", () => ({
        type: "url",
        ar_url: "https://example.com/assets/model.glb",
        ar_placement: "wall",
        auto_rotate: false,
    }));

    await startInteractions(PRODUCT_PAGE_HTML);

    await click('.product_images[data-type="3d"]');
    await tick();

    const modelViewer = queryOne("#model-viewer");
    expect(modelViewer.getAttribute("src")).toBe("https://example.com/assets/model.glb");
    expect(modelViewer.getAttribute("ar-placement")).toBe("wall");
    expect(modelViewer.hasAttribute("auto-rotate")).toBe(false);
});

test("CarouselSlider.prototype.prefetchImages handles null elements gracefully", () => {
    const itemEl = document.createElement("div");
    const imgEl = document.createElement("img");
    imgEl.setAttribute("loading", "lazy");
    itemEl.appendChild(imgEl);

    const slider = Object.create(CarouselSlider.prototype);
    slider.prefetchImages([null, undefined, itemEl]);

    expect(imgEl.hasAttribute("loading")).toBe(false);
});
