odoo.define('theme_eco_refine.about_us', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    /**
     * Widget for displaying about-us page.
     */
    publicWidget.registry.refurb_theme_about_us = publicWidget.Widget.extend({
        templates: 'theme_eco_refine.about_us',
        selector: '.ref-wrapper', // Replace this selector with the appropriate one for your tab container
        events: {
        'click .ref-abt-button': 'toggleDiv',
        'click .ref-mob-btn': 'toggleContent',
        'click .custom-nav_prev': 'togglePrevious',
        'click .custom-nav_next': 'toggleNext',
    },

    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
        var defaultIndex = 2;
        var defaultContentElement = document.querySelector('.ref-abt_mob .ref-mob-btn:nth-child(' + (defaultIndex + 1) + ') .ref-abt-button__mobcontent');
        if (defaultContentElement){
            defaultContentElement.classList.add('show');
        }

        const buttons = self.$el[0].querySelectorAll('.ref-abt-button');
        if (buttons.length > 0){
            buttons[1].classList.add('active');
            buttons[3].classList.add('active');
        }
        self.$(".owl-carousel-abt").owlCarousel();
        });
    },

    toggleDiv: function (ev) {
        const buttons = this.$el[0].querySelectorAll('.ref-abt-button');
        const about = ev.target.querySelector('.ref-abt-button__content');
        buttons.forEach((btn) => {
        btn.classList.remove('active');
        btn.querySelector('.ref-abt-button__content').style.display = 'none';
      });
       ev.target.classList.add('active');
       about.style.display = 'block';
    },

    toggleContent: function (ev){
        let index;
       if($(ev.target).hasClass('div0')){
            index = 0
       }else if($(ev.target).hasClass('div1')){
            index = 1
       }else if($(ev.target).hasClass('div2')){
            index = 2
       }else if($(ev.target).hasClass('div3')){
            index = 3
       }else {
            index = 4
       }
        const contentElements = this.$el[0].querySelectorAll('.ref-abt-button__mobcontent');
        contentElements.forEach(function (contentElement, i) {
        if (i === index) {
          contentElement.classList.add('show');
        } else {
          contentElement.classList.remove('show');
        }
      });

      const buttonTextElements = this.$el[0].querySelectorAll('.button-mob-text');
      buttonTextElements.forEach(function (buttonTextElement, i) {
        if (i === index) {
          buttonTextElement.classList.toggle('hidden');
        } else {
          buttonTextElement.classList.remove('hidden');
        }
      });


    },

    togglePrevious:function(){
         this.$(".owl-carousel-abt").trigger("prev.owl.carousel");
    },

    toggleNext:function(){
         this.$(".owl-carousel-abt").trigger("next.owl.carousel");
    },

    });
    return publicWidget.registry.refurb_theme_about_us;
});
