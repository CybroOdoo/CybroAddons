import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export const RecommendationBusListener = {
    dependencies: ["bus_service"],
    start(env) {
        const bus = env.services.bus_service;

        async function waitForContainer(timeout = 3000) {
            return new Promise((resolve) => {
                const startTime = performance.now();
                const check = () => {
                    const el = document.getElementById("reco-slider");
                    if (el) {
                        resolve(el);
                    } else if (performance.now() - startTime < timeout) {
                        requestAnimationFrame(check);
                    } else {
                        resolve(null);
                    }
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

            if (btnLeft) {
                btnLeft.addEventListener("click", () => {
                    clearInterval(interval);
                    prevPage();
                    interval = setInterval(nextPage, delay);
                });
            }

            if (btnRight) {
                btnRight.addEventListener("click", () => {
                    clearInterval(interval);
                    nextPage();
                    interval = setInterval(nextPage, delay);
                });
            }

            window.addEventListener("resize", () => {
                slider.scrollTo({ left: pageWidth * currentPage, behavior: "instant" });
            });
        }

        let isRendered = false;

        async function renderRecommendations(products) {
            isRendered = true;
            const container = document.querySelector(".position-relative");
            const loader = document.getElementById("reco-loading");
            if (loader) loader.remove();

            if (!products || !products.length) return;

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
                        const link = document.createElement("a");
                        link.href = `/shop/product/${prod.product_id}`;

                        if (prod.image) {
                            const img = document.createElement("img");
                            img.src = prod.image;
                            img.className = "card-img-top";
                            img.style.objectFit = "cover";
                            img.style.height = "180px";
                            link.appendChild(img);
                        }

                        const cardBody = document.createElement("div");
                        cardBody.className = "card-body";

                        const title = document.createElement("h6");
                        title.className = "card-title text-truncate";
                        title.textContent = prod.display_text || prod.name || "";

                        const price = document.createElement("p");
                        price.className = "text-muted mb-0";
                        price.textContent = `${prod.currency || ""} ${prod.list_price || ""}`.trim();

                        cardBody.appendChild(title);
                        cardBody.appendChild(price);

                        card.appendChild(link);
                        card.appendChild(cardBody);
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
                console.error("Failed to load stored recommendations", err);
            }
        }

        (async () => {
            const container = await waitForContainer();
            if (!container) {
                return;
            }
            bus.start();
            bus.subscribe("notifications", (notifications) => {
                if (!notifications || !notifications.length) {
                    const loader = document.getElementById("reco-loading");
                    if (loader) loader.remove();
                    return;
                }
                renderRecommendations(notifications);
            });
            setTimeout(loadSessionRecommendations, 500);
            setTimeout(() => {
                if (!isRendered) {
                    const loader = document.getElementById("reco-loading");
                    if (loader) loader.remove();
                }
            }, 5000);
        })();
    },
};

registry.category("services").add("recommendation_product_ai", RecommendationBusListener);

