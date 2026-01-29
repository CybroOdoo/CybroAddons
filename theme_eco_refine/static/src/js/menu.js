odoo.define('theme_eco_refine.custom', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
     /**
     * Product Details Tab.
     */
    publicWidget.registry.refurb_theme_product = publicWidget.Widget.extend({
        templates: 'website_sale.product',
        selector: '.tab', // Replace this selector with the appropriate one for your tab container
        events: {
        'click .tab-link': 'openTab',
    },
    openTab: function (ev) {
        let tabId;
       if($(ev.target).hasClass('tab1')){
            tabId = "tab1"
       }else{
          tabId = "tab2"
       }
      var tabContent = this.$(".tab-content");
      var tabLinks = this.$(".tab-link");

      for (var i = 0; i < tabContent.length; i++) {
        tabContent[i].style.display = "none";
      }

      for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
      }
      if(tabId){
      document.getElementById(tabId).style.display = "block";
      }
      ev.target.classList.add("active");
    }
    });
    return publicWidget.registry.refurb_theme_product;
});
