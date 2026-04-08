/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.nutritionWidget = publicWidget.Widget.extend({
    selector : '#nutritional_info',
    events: {
        'click #button_nutrition': '_onClickNutrition',
        'click #button_ingredients': '_onClickIngredient',
        'click #button_allergy': '_onClickAllergy',
        'click #show_nutrition': '_onClickShowNutrition',
    },

    start: function () {
        const self = this;
        const base_url = this.target.baseURI;
        const demo = base_url.split("/");
        const product_id = demo[4];

        // Init hide
        this.$el.find("#product_ingredients, #product_allergy, #per_person").hide();
        this.$el.find("#button_nutrition, #button_ingredients, #button_allergy").hide();
        this.$el.find("#show_nutrition").hide();

        // Track which ones have data
        this._nutritionDataMap = {
            nutrition: false,
            ingredients: false,
            allergy: false
        };

        this._isDataReady = false;

        const nutritionPromise = rpc("/shop/product_nutrition_details", { name: product_id }).then(function (nutrition) {
            if (nutrition && nutrition.length > 0) {
                self._nutritionDataMap.nutrition = true;
            }
        });

        const ingredientsPromise = rpc("/shop/product_ingredients_details", { name: product_id }).then(function (ingredients_information) {

            if (ingredients_information && ingredients_information.trim().length > 0) {
                self._nutritionDataMap.ingredients = true;
            }
        });

        const allergyPromise = rpc("/shop/product_allergy_details", { name: product_id }).then(function (allergy_information) {
            if (allergy_information && allergy_information.trim().length > 0) {
                self._nutritionDataMap.allergy = true;
            }
        });
        Promise.all([nutritionPromise, ingredientsPromise, allergyPromise]).then(function () {
            const hasAnyData = Object.values(self._nutritionDataMap).some(Boolean);
            if (hasAnyData) {
                self._isDataReady = true;  // ✅ Mark data as ready
                self.$el.find("#show_nutrition").show();
            }
        });
        return this._super.apply(this, arguments);
    },

    _onClickShowNutrition : function(ev) {
    if (!this._isDataReady) return;

    const $el = this.$el;
    const map = this._nutritionDataMap;

    const $btnNutrition = $el.find("#button_nutrition");
    const $btnIngredients = $el.find("#button_ingredients");
    const $btnAllergy = $el.find("#button_allergy");

    // Toggle buttons
    if (map.nutrition) $btnNutrition.toggle();
    if (map.ingredients) $btnIngredients.toggle();
    if (map.allergy) $btnAllergy.toggle();

    // Check if buttons are visible (i.e., we're showing or hiding)
    const isVisible = $btnNutrition.is(":visible") || $btnIngredients.is(":visible") || $btnAllergy.is(":visible");

    if (!isVisible) {
        // If hiding buttons, also hide all content sections
        $el.find("#product_allergy, #product_ingredients, #per_person").hide().empty();
    }
},
    _onClickNutrition: function (ev) {
        const $el = this.$el;
        const $nutritionDiv = $el.find("#per_person");

        if ($nutritionDiv.is(":visible")) {
            $nutritionDiv.hide().empty();
            return;
        }

        $nutritionDiv.empty().show();
        const product_id = this.target.baseURI.split("/")[4];

        rpc("/shop/product_nutrition_details", { name: product_id }).then(function (nutrition) {
            $el.find("#product_allergy, #product_ingredients").empty().hide();
            $.each(nutrition, function(index, value) {
                $nutritionDiv.append(
                    `<div>${value['name']}: ${value['nutrition_value']} ${value['uom_name']}</div>`
                );
            });
        });
    },

   _onClickIngredient: function (ev) {
    const $el = this.$el;
    const $ingredientDiv = $el.find("#product_ingredients");

    if ($ingredientDiv.is(":visible")) {
        $ingredientDiv.hide().empty();
        return;
    }

    $ingredientDiv.empty().show();
    const product_id = this.target.baseURI.split("/")[4];

    rpc("/shop/product_ingredients_details", { name: product_id }).then(function (ingredients_information) {
        $el.find("#product_allergy, #per_person").empty().hide();
        $ingredientDiv.append(ingredients_information);
    });
},


   _onClickAllergy: function (ev) {
    const $el = this.$el;
    const $allergyDiv = $el.find("#product_allergy");

    if ($allergyDiv.is(":visible")) {
        $allergyDiv.hide().empty();
        return;
    }

    $allergyDiv.empty().show();
    const product_id = this.target.baseURI.split("/")[4];

    rpc("/shop/product_allergy_details", { name: product_id }).then(function (allergy_information) {
        $el.find("#product_ingredients, #per_person").empty().hide();
        $allergyDiv.append(allergy_information);
    });
},

});

return publicWidget.registry.nutritionWidget;
