/**
 * Custom JavaScript functionality for the Diva theme's homepage.
 *
 * This module defines various interactive features and behaviors for the Diva theme's homepage.
 * It includes functions for lazy loading images, scroll animations, email validation, accordion panels,
 * magnifier zoom, quantity controls, preloader, color customization, and direction switching.
 *
 * @module theme_diva.index
 */
odoo.define('theme_diva.index', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var MyCustomWidget = Widget.extend({
   /**
     * Starts the custom widget by initializing various features and behaviors.
     */
    start: function() {
      this._initializeImgLazyLoad();
      this._initializeScrollAnimation('.show-on-scroll', 'is-visible');
      this._initializeScrollAnimation('.wrapp', 'wrappit');
      this._initializeScrollFunction();
      this._initializeEmailValidation();
      this._initializeAccordion();
      this._initializeMagnifier();
      this._initializeQuantityControls();
      this._initializePreloader();
      this._initializeColorChanger();
      this._initializeDirectionSwitch();
      this._initializeAOS();
    },
    _initializeImgLazyLoad: function() {
      $(".img_lazy").ImgLazyLoad({
        mobile: "640",
        qhd: "1680",
        offset: "-150",
        time: "550",
        animateOut: 'img_lazy'
      });
    },
    _initializeScrollAnimation: function(selector, className) {
      var self = this;
      var elementsToShow = document.querySelectorAll(selector);
      function loop() {
        Array.prototype.forEach.call(elementsToShow, function(element) {
          if (self._isElementInViewport(element)) {
            element.classList.add(className);
          }
        });
        self._scroll(loop);
      }
      loop();
    },
    _scroll: function(callback) {
      var scroll = window.requestAnimationFrame || function(callback) {
        window.setTimeout(callback, 1000 / 90);
      };
      scroll(callback);
    },
    _isElementInViewport: function(el) {
      var rect = el.getBoundingClientRect();
      return (
        (rect.top <= 0 && rect.bottom >= 0) ||
        (rect.bottom >= (window.innerHeight || document.documentElement.clientHeight) &&
          rect.top <= (window.innerHeight || document.documentElement.clientHeight)) ||
        (rect.top >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight))
      );
    },
    _initializeScrollFunction: function() {
      var self = this;
      window.onscroll = function() {
        self._scrollFunction();
      };
    },
    _scrollFunction: function() {
      if (document.body.scrollTop > 80 || document.documentElement.scrollTop > 80) {
        document.getElementById("new").style.top = "0px";
      } else {
        document.getElementById("new").style.top = "205px";
      }
    },
    _initializeEmailValidation: function() {
      var self = this;
      var textEmail = document.getElementById("textEmail");
      var demo = document.getElementById("demo");
      var emailButton = document.getElementById("emailButton");
      emailButton.addEventListener("click", function() {
        self._validateEmail(textEmail, demo);
      });
    },
    _validateEmail: function(emailInput, demoElement) {
      var email = emailInput.value;
      var reg = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
      if (reg.test(emailInput.value) == false) {
        demoElement.style.color = "#535353";
        demoElement.style.padding = "8px 0px";
        demoElement.innerHTML = " The email you entered isn't valid.." + email;
        return false;
      } else {
        demoElement.style.color = "#50449c";
        demoElement.style.padding = "8px 0px";
        demoElement.innerHTML = "<i class='fas fa-hand-point-right'></i> <strong>  WOOHOO</strong> You subscribed successfully.. " + email;
      }
      return true;
    },
    _initializeAccordion: function() {
      var acc = document.getElementsByClassName("accordion");
      for (var i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function() {
          this.classList.toggle("active");
          var panel = this.nextElementSibling;
          if (panel.style.display === "block") {
            panel.style.display = "none";
          } else {
            panel.style.display = "block";
          }
        });
      }
    },
    _initializeMagnifier: function() {
      var mzOptions = {
        expand: 'fullscreen',
        rightClick: 'true',
        zoomOn: 'true',
        zoomMode: 'magnifier'
      };
      $('#zoom_05').ezPlus({
        zoomType: 'inner',
        cursor: 'crosshair'
      });
    },
    _initializeQuantityControls: function() {
      var self = this;
      $('.quantity-right-plus').click(function(e) {
        e.preventDefault();
        self._incrementQuantity();
      });
      $('.quantity-left-minus').click(function(e) {
        e.preventDefault();
        self._decrementQuantity();
      });
    },
    _incrementQuantity: function() {
      var quantity = parseInt($('#quantity').val());
      $('#quantity').val(quantity + 1);
    },
    _decrementQuantity: function() {
      var quantity = parseInt($('#quantity').val());
      if (quantity > 0) {
        $('#quantity').val(quantity - 1);
      }
    },
    _initializePreloader: function() {
      var self = this;
      setTimeout(function() {
        self._loadPreloader();
      }, 3000);
    },
    _loadPreloader: function() {
      $('#ctn-preloader').addClass('loaded');
      $('body').removeClass('no-scroll-y');
      if ($('#ctn-preloader').hasClass('loaded')) {
        $('#preloader').delay(1000).queue(function() {
          $(this).remove();
        });
      }
    },
    _initializeColorChanger: function() {
      var self = this;
      var color1 = document.querySelector(".color1");
      var color2 = document.querySelector(".color2");
      var primaryColorInput = document.querySelector(".primaryColor");
      var secondaryColorInput = document.querySelector(".secondoryColor");
      var buttonColorInput = document.querySelector(".buttonColor");
      var footerColorInput = document.querySelector(".footerColor");
      self._eventSetter(color1, "input", function(e) {
        self._setPrimaryGradient(color1.value, color2.value);
      });
      self._eventSetter(color2, "input", function(e) {
        self._setPrimaryGradient(color1.value, color2.value);
      });
      self._eventSetter(primaryColorInput, "input", function(e) {
        self._setSolidColor('--primar-color', primaryColorInput.value);
      });
      self._eventSetter(secondaryColorInput, "input", function(e) {
        self._setSolidColor('--secondary-color', secondaryColorInput.value);
      });
      self._eventSetter(buttonColorInput, "input", function(e) {
        self._setSolidColor('--button-color', buttonColorInput.value);
      });
      self._eventSetter(footerColorInput, "input", function(e) {
        self._setSolidColor('--footer-color', footerColorInput.value);
      });
    },
    _eventSetter: function(el, event, fn) {
      el.addEventListener(event, fn);
    },
    _setPrimaryGradient: function(color1, color2) {
      let root = document.documentElement;
      root.style.setProperty('--primar-gradient-color-one', color1);
      root.style.setProperty('--primar-gradient-color-two', color2);
    },
    _setSolidColor: function(cssProperty, color) {
      let root = document.documentElement;
      root.style.setProperty(cssProperty, color);
    },
    _initializeDirectionSwitch: function() {
      var self = this;
      var directionSwitch = document.getElementById('directionSwitch');
      directionSwitch.addEventListener('click', function() {
        self._toggleDirection();
      });
    },
    _toggleDirection: function() {
      var docDirection = document.documentElement.dir;
      var isRTL = (docDirection === 'rtl');
      document.documentElement.dir = isRTL ? 'ltr' : 'rtl';
    },
    _initializeAOS: function() {
      AOS.init({
        duration: 800,
        once: true
      });
    }
  });
  core.action_registry.add('theme_diva.index', MyCustomWidget);
});
