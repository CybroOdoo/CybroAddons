/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class NutritionWidget extends Interaction {
    static selector = "#nutritional_info";

    dynamicContent = {
        "#button_nutrition": {
            "t-on-click": this._onClickNutrition,
        },
        "#button_ingredients": {
            "t-on-click": this._onClickIngredient,
        },
        "#button_allergy": {
            "t-on-click": this._onClickAllergy,
        },
        "#show_nutrition": {
            "t-on-click.prevent": this._onClickShowNutrition,
        },
    };

    _getProductSlug() {
        const pathParts = window.location.pathname.replace(/\/$/, "").split("/").filter(Boolean);
        return pathParts[pathParts.length - 1] || "";
    }

    setup() {
        this._nutritionDataMap = {
            nutrition: false,
            ingredients: false,
            allergy: false,
        };
        this._isDataReady = false;

        const ingredientsEl = this.el.querySelector("#product_ingredients");
        const allergyEl = this.el.querySelector("#product_allergy");
        const perPersonEl = this.el.querySelector("#per_person");
        const btnNutrition = this.el.querySelector("#button_nutrition");
        const btnIngredients = this.el.querySelector("#button_ingredients");
        const btnAllergy = this.el.querySelector("#button_allergy");
        const showNutritionBtn = this.el.querySelector("#show_nutrition");

        if (ingredientsEl) ingredientsEl.style.display = "none";
        if (allergyEl) allergyEl.style.display = "none";
        if (perPersonEl) perPersonEl.style.display = "none";
        if (btnNutrition) btnNutrition.style.display = "none";
        if (btnIngredients) btnIngredients.style.display = "none";
        if (btnAllergy) btnAllergy.style.display = "none";
        if (showNutritionBtn) showNutritionBtn.style.display = "none";

        const productId = this._getProductSlug();

        const nutritionPromise = rpc("/shop/product_nutrition_details", { name: productId }).then(
            (nutrition) => {
                if (nutrition && nutrition.length > 0) {
                    this._nutritionDataMap.nutrition = true;
                }
            }
        );

        const ingredientsPromise = rpc("/shop/product_ingredients_details", { name: productId }).then(
            (ingredients) => {
                if (ingredients && typeof ingredients === "string" && ingredients.trim().length > 0) {
                    this._nutritionDataMap.ingredients = true;
                }
            }
        );

        const allergyPromise = rpc("/shop/product_allergy_details", { name: productId }).then(
            (allergy) => {
                if (allergy && typeof allergy === "string" && allergy.trim().length > 0) {
                    this._nutritionDataMap.allergy = true;
                }
            }
        );

        Promise.all([nutritionPromise, ingredientsPromise, allergyPromise]).then(() => {
            const hasAnyData = Object.values(this._nutritionDataMap).some(Boolean);
            if (hasAnyData) {
                this._isDataReady = true;
                if (showNutritionBtn) showNutritionBtn.style.display = "";
            }
        });
    }

    _onClickShowNutrition() {
        if (!this._isDataReady) return;

        const map = this._nutritionDataMap;
        const btnNutrition = this.el.querySelector("#button_nutrition");
        const btnIngredients = this.el.querySelector("#button_ingredients");
        const btnAllergy = this.el.querySelector("#button_allergy");

        const toggleDisplay = (el, hasData) => {
            if (!el || !hasData) return;
            el.style.display = el.style.display === "none" ? "" : "none";
        };

        toggleDisplay(btnNutrition, map.nutrition);
        toggleDisplay(btnIngredients, map.ingredients);
        toggleDisplay(btnAllergy, map.allergy);

        const isAnyVisible =
            (btnNutrition && btnNutrition.style.display !== "none") ||
            (btnIngredients && btnIngredients.style.display !== "none") ||
            (btnAllergy && btnAllergy.style.display !== "none");

        if (!isAnyVisible) {
            const allergyEl = this.el.querySelector("#product_allergy");
            const ingredientsEl = this.el.querySelector("#product_ingredients");
            const perPersonEl = this.el.querySelector("#per_person");

            if (allergyEl) { allergyEl.style.display = "none"; allergyEl.replaceChildren(); }
            if (ingredientsEl) { ingredientsEl.style.display = "none"; ingredientsEl.replaceChildren(); }
            if (perPersonEl) { perPersonEl.style.display = "none"; perPersonEl.replaceChildren(); }
        }
    }

    async _onClickNutrition() {
        const perPersonEl = this.el.querySelector("#per_person");
        if (!perPersonEl) return;

        if (perPersonEl.style.display !== "none" && perPersonEl.children.length > 0) {
            perPersonEl.style.display = "none";
            perPersonEl.replaceChildren();
            return;
        }

        perPersonEl.replaceChildren();
        perPersonEl.style.display = "";
        const productId = this._getProductSlug();

        const nutrition = await rpc("/shop/product_nutrition_details", { name: productId });
        const allergyEl = this.el.querySelector("#product_allergy");
        const ingredientsEl = this.el.querySelector("#product_ingredients");
        if (allergyEl) { allergyEl.style.display = "none"; allergyEl.replaceChildren(); }
        if (ingredientsEl) { ingredientsEl.style.display = "none"; ingredientsEl.replaceChildren(); }

        if (nutrition && Array.isArray(nutrition)) {
            for (const value of nutrition) {
                const div = document.createElement("div");
                div.textContent = `${value.name}: ${value.nutrition_value} ${value.uom_name || ""}`;
                perPersonEl.appendChild(div);
            }
        }
    }

    async _onClickIngredient() {
        const ingredientsEl = this.el.querySelector("#product_ingredients");
        if (!ingredientsEl) return;

        if (ingredientsEl.style.display !== "none" && ingredientsEl.children.length > 0) {
            ingredientsEl.style.display = "none";
            ingredientsEl.replaceChildren();
            return;
        }

        ingredientsEl.replaceChildren();
        ingredientsEl.style.display = "";
        const productId = this._getProductSlug();

        const ingredientsInfo = await rpc("/shop/product_ingredients_details", { name: productId });
        const allergyEl = this.el.querySelector("#product_allergy");
        const perPersonEl = this.el.querySelector("#per_person");
        if (allergyEl) { allergyEl.style.display = "none"; allergyEl.replaceChildren(); }
        if (perPersonEl) { perPersonEl.style.display = "none"; perPersonEl.replaceChildren(); }

        if (ingredientsInfo) {
            ingredientsEl.innerHTML = ingredientsInfo;
        }
    }

    async _onClickAllergy() {
        const allergyEl = this.el.querySelector("#product_allergy");
        if (!allergyEl) return;

        if (allergyEl.style.display !== "none" && allergyEl.children.length > 0) {
            allergyEl.style.display = "none";
            allergyEl.replaceChildren();
            return;
        }

        allergyEl.replaceChildren();
        allergyEl.style.display = "";
        const productId = this._getProductSlug();

        const allergyInfo = await rpc("/shop/product_allergy_details", { name: productId });
        const ingredientsEl = this.el.querySelector("#product_ingredients");
        const perPersonEl = this.el.querySelector("#per_person");
        if (ingredientsEl) { ingredientsEl.style.display = "none"; ingredientsEl.replaceChildren(); }
        if (perPersonEl) { perPersonEl.style.display = "none"; perPersonEl.replaceChildren(); }

        if (allergyInfo) {
            allergyEl.innerHTML = allergyInfo;
        }
    }
}

registry.category("public.interactions").add("product_nutrition_allergen.website_sale", NutritionWidget);

