// const body = document.body;
//const progressBar = document.querySelector('.progress-bar');
//
//function stretch() {
//  const pixelScrolled = window.scrollY;
//  const viewportHeight = window.innerHeight;
//  const totalContentHeight = document.body.scrollHeight;
//
//  // convert pixel to percentage
//  const pixelToPerc = (pixelScrolled / (totalContentHeight - viewportHeight)) * 100;
//
//  // set width to the progress bar
//  progressBar.style.width = Math.round(pixelToPerc) + '%';
//}
//
//// scroll event
//window.addEventListener('scroll', stretch);

odoo.define('theme_zen_dark.progress_bar',function(require){
'use strict';

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    sAnimation.registry.progress_bar = sAnimation.Class.extend({
    selector : '.progress-bar',
    disabledInEditableMode: false,
    start: function () {
        var self = this;
        self.initialize_owl();
    },

    initialize_owl: function (autoplay=true) {

        window.addEventListener('scroll', this.stretch);

    },

    stretch: function () {
      const progressBar = document.querySelector('.progress-bar');
      const pixelScrolled = window.scrollY;
      const viewportHeight = window.innerHeight;
      const totalContentHeight = document.body.scrollHeight;

      // convert pixel to percentage
      const pixelToPerc = (pixelScrolled / (totalContentHeight - viewportHeight)) * 100;

      // set width to the progress bar
      progressBar.style.width = Math.round(pixelToPerc) + '%';

    },
    });

});

