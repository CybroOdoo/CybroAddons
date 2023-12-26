/** @odoo-module **/
import publicWidget from 'web.public.widget';
var ajax=require('web.ajax');
var rpc=require('web.rpc');
publicWidget.registry.nutritionWidget = publicWidget.Widget.extend({
     selector : '#nutritional_info',
    events: {
        'click #button_nutrition': '_onClickNutrition',
        'click #button_ingredients': '_onClickIngredient',
        'click #button_allergy' : '_onClickAllergy',
        'click #show_nutrition' : '_onClickShowNutrition',
    },
     start: function () {
     // Hide all buttons and divs while loading
     this.$el.find("#product_ingredients").empty();
     this.$el.find("#product_ingredients").hide();
     this.$el.find("#product_allergy").empty();
     this.$el.find("#product_allergy").hide();
      this.$el.find("#per_person").empty();
      this.$el.find("#per_person").hide();
      this.$el.find("#button_nutrition").hide();
      this.$el.find("#button_ingredients").hide();
      this.$el.find("#button_allergy").hide();
      },
      _onClickShowNutrition : function(ev) {
      // Function to display nutritional information buttons
      var div_selector = this.$el
      div_selector.find("#button_nutrition").toggle();
      div_selector.find("#button_ingredients").toggle();
      div_selector.find("#button_allergy").toggle();
      },
     _onClickNutrition: function (ev) {
     // Function to display product nutrition  details
     var div_selector = this.$el;
     div_selector.find("#per_person").empty();
     div_selector.find("#per_person").show();
     var base_url = this.target.baseURI
     var demo = base_url.split("/");
     rpc.query({
            model: 'product.template',
            method: 'product_nutrition_details',
            args: [demo[4]]
        }).then(function (nutrition) {
        $.each(nutrition, function( index, value ) {
         div_selector.find("#product_allergy").empty();
        div_selector.find("#product_ingredients").empty();
        div_selector.find("#per_person").append("<div>"+value['name']+":"+value['nutrition_value']+" "+value['uom_name']+"</div>");
        });
     });
    },
   _onClickIngredient : function (ev) {
    // Function to display product ingredient details
    var div_selector = this.$el;
    div_selector.find("#product_ingredients").show();
     var base_url = this.target.baseURI
     var demo = base_url.split("/");
     rpc.query({
            model: 'product.template',
            method: 'product_ingredients_details',
            args: [demo[4]]
        }).then(function (ingredients_information) {
        div_selector.find("#product_ingredients").empty();
        div_selector.find("#product_allergy").empty();
        div_selector.find("#per_person").empty();
        div_selector.find("#product_ingredients").append(ingredients_information);
     });
    },
    _onClickAllergy : function (ev) {
    // Function to print product allergen information
    var div_selector = this.$el;
    div_selector.find("#product_allergy").show();
     var base_url = this.target.baseURI
     var demo = base_url.split("/");
     rpc.query({
            model: 'product.template',
            method: 'product_allergy_details',
            args: [demo[4]]
        }).then(function (allergy_information) {
        div_selector.find("#product_allergy").empty();
        div_selector.find("#product_ingredients").empty();
        div_selector.find("#per_person").empty();
        div_selector.find("#product_allergy").append(allergy_information);
     });
    },
     });
     return publicWidget.registry.nutritionWidget;
