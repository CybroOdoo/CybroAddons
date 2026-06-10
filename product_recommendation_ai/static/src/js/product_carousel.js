/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export const RecommendationBusListener = {
    dependencies: ["bus_service"],
    start(env) {
        const bus = env.services.bus_service;
        const channel = "reco_channel";
        bus.addChannel(channel);

        async function waitForContainer() {
            return new Promise(resolve => {
                const check = () => {
                    const el = document.getElementById("reco-slider");
                    if (el) resolve(el);
                    else requestAnimationFrame(check);
                };
                check();
            });
        }

        function enableButtonsAndAutoScroll(slider) {
            const btnLeft = document.getElementById("reco-left");
            const btnRight = document.getElementById("reco-right");
            const pages = [...slider.querySelectorAll(".reco-page")];
            if (!pages.length) return;
            const pageWidth = slider.clientWidth;
            const totalReal = pages.length - 2;
            let currentPage = 1;
            slider.scrollTo({ left: pageWidth * currentPage, behavior: "instant" });
            const delay = 3000;
            let interval = setInterval(nextPage, delay);

            function goToPage(index, instant = false) {
                currentPage = index;
                slider.scrollTo({
                    left: pageWidth * index,
                    behavior: instant ? "instant" : "smooth",
                });
            }

            function nextPage() {
                currentPage++;
                goToPage(currentPage);
                if (currentPage === pages.length - 1) {
                    setTimeout(() => goToPage(1, true), 350);
                }
            }

            function prevPage() {
                currentPage--;
                goToPage(currentPage);

                if (currentPage === 0) {
                    setTimeout(() => goToPage(totalReal, true), 350);
                }
            }

            btnLeft.addEventListener("click", () => {
                clearInterval(interval);
                prevPage();
                interval = setInterval(nextPage, delay);
            });

            btnRight.addEventListener("click", () => {
                clearInterval(interval);
                nextPage();
                interval = setInterval(nextPage, delay);
            });

            window.addEventListener("resize", () => {
                slider.scrollTo({ left: pageWidth * currentPage, behavior: "instant" });
            });
        }

        async function renderRecommendations(products) {
            const container = document.querySelector(".position-relative");
            const loader = document.getElementById("reco-loading");
            if (loader) loader.remove();

            let slider = document.getElementById("reco-slider");
            if (!slider) {
                slider = document.createElement("div");
                slider.id = "reco-slider";
                slider.className = "d-flex flex-row flex-nowrap py-2";
                slider.style.scrollBehavior = "smooth";
                container.appendChild(slider);
            }
            slider.style.display = "flex";
            slider.innerHTML = "";

            const pageSize = 4;
            const totalPages = Math.ceil(products.length / pageSize);
            const pages = [];

            for (let p = 0; p < totalPages; p++) {
                const page = document.createElement("div");
                page.className = "reco-page";
                page.style.display = "flex";
                page.style.gap = "16px";
                page.style.minWidth = "100%";
                page.style.boxSizing = "border-box";

                const group = products.slice(p * pageSize, (p + 1) * pageSize);
                while (group.length < 4) group.push(null);

                group.forEach(prod => {
                    const card = document.createElement("div");
                    card.className = "reco-card card shadow-sm";
                    card.style.flex = "1";

                    if (prod) {
                        card.innerHTML = `
                            <a href="/shop/product/${prod.product_id}">
                                <img src="${prod.image}" class="card-img-top"
                                     style="object-fit: cover; height: 180px;">
                            </a>
                            <div class="card-body">
                                <h6 class="card-title text-truncate">${prod.display_text || prod.name}</h6>
                                <p class="text-muted mb-0">${prod.currency} ${prod.list_price}</p>
                            </div>
                        `;
                    } else {
                        card.style.visibility = "hidden";
                    }
                    page.appendChild(card);
                });

                slider.appendChild(page);
                pages.push(page);
            }
            const lastClone = pages[pages.length - 1].cloneNode(true);
            slider.prepend(lastClone);
            const firstClone = pages[0].cloneNode(true);
            slider.appendChild(firstClone);
            enableButtonsAndAutoScroll(slider);
        }

        async function loadSessionRecommendations() {
            try {
                const stored = await rpc("/recommendation/session/get", {});
                if (stored && stored.length) {
                    renderRecommendations(stored);
                }
            } catch (err) {
            }
        }

        (async () => {
            await waitForContainer();
            bus.subscribe("notifications", (notifications) => {
                if (!notifications.length) return;
                renderRecommendations(notifications);
            });
            setTimeout(loadSessionRecommendations, 500);
        })();
    },
};
registry.category("services").add("recommendation_product_ai", RecommendationBusListener);
