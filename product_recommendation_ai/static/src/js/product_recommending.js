/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export const RecommendationBusListener = {
    dependencies: ["bus_service"],

    start(env) {
        const bus = env.services.bus_service;
        const CHANNEL = "reco_channel";
        bus.addChannel(CHANNEL);

        function waitForContainer() {
            return new Promise((resolve) => {
                const check = () => {
                    const el = document.getElementById("recommendation-container");
                    if (el) resolve(el);
                    else requestAnimationFrame(check);
                };
                check();
            });
        }

        async function renderRecommendations(products) {
            const container = await waitForContainer();
            if (!products || !products.length) {
                container.innerHTML = `<p class="text-muted">No recommendations available</p>`;
                return;
            }
            container.innerHTML = products.map((product) => {
                const tmplId = product.product_id || "";
                const img = product.image
                    ? `<img src="${product.image}" class="img-fluid object-fit-contain" />`
                    : `<span class="text-muted">No Image</span>`;
                return `
                    <div class="col-md-3 mb-3">
                        <div class="card h-100 shadow-sm border-0">
                            <div class="ratio ratio-1x1 d-flex align-items-center justify-content-center bg-light">
                                ${img}
                            </div>
                            <div class="card-body text-center">
                                <h6 class="card-title fw-semibold text-truncate">${product.name}</h6>
                                <p class="text-muted mb-3">${product.currency} ${product.list_price}</p>
                                <a href="/shop/product/${tmplId}"
                                   class="btn btn-sm btn-outline-primary rounded-pill px-3">
                                   View
                                </a>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }

        async function saveSessionRecommendations(products) {
            try {
                await rpc("/recommendation/session/save", { products });
            } catch (e) {
               console.error("Failed to save session recommendations", e);            }
        }

        async function loadSessionRecommendations() {
            try {
                const stored = await rpc("/recommendation/session/get", {});

                if (stored && stored.length) {
                    renderRecommendations(stored);
                } else {
                    const container = await waitForContainer();
                    container.innerHTML = `<p class="text-muted">No recommendations available</p>`;
                }
            } catch (e) {
                console.error("Failed to load session recommendations", e);
            }
        }

        let busMessageReceived = false;
        bus.subscribe(CHANNEL, async (payload) => {
            busMessageReceived = true;
            renderRecommendations(payload);
            saveSessionRecommendations(payload);
            sessionStorage.setItem("recommendations", JSON.stringify(payload));
        });

        (async () => {
            await waitForContainer();
            const BUS_WAIT_MS = 2000;
            setTimeout(() => {
                if (!busMessageReceived) {
                    loadSessionRecommendations();
                }
            }, BUS_WAIT_MS);
        })();

        document.addEventListener("DOMContentLoaded", async () => {
            const storedProducts = sessionStorage.getItem("recommendations");
            if (storedProducts) {
                renderRecommendations(JSON.parse(storedProducts));
            }
        });
    }
};
registry.category("services").add("recommendation_product", RecommendationBusListener);
