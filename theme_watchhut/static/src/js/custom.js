/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
/**
 * Created ScrollAnimation widget
 * To make available the animation opacity affect on the snippet gallery on
 * scrolling the window here added event wheel effect to achieve the animation
 **/
publicWidget.registry.ScrollAnimation = publicWidget.Widget.extend({
  selector: '.images',
  events: {
    'wheel': 'onScroll',
    'scroll': 'onScroll',
  },
  // In start function called the function onScroll();
  start: function () {
    this.onScroll();
    // Also listen to window scroll to catch page-level scrolling
    window.addEventListener('scroll', this.onScroll.bind(this));
    return this._super.apply(this, arguments);
  },
  /**This function is triggered whenever window is scrolled
      image variable stores images with class .inline-photo
      and check in isElementInViewport(args) function
  **/
  onScroll: function () {
    var images = document.querySelectorAll('.inline-photo');
    var self = this;
    Array.prototype.forEach.call(images, function (element) {
      if (self.isElementInViewport(element)) {
        element.classList.add('is-visible');
      } else {
        element.classList.remove('is-visible');
      }
    });
  },
  /**  This function checks if each picture is present in the viewport
       and if present it is made visible
  **/
  isElementInViewport: function (el) {
    var rect = el.getBoundingClientRect();
    return (
      (rect.top <= (window.innerHeight || document.documentElement.clientHeight) && rect.bottom >= 0)
    );
  }
});

/**
 * Contact Form Validation
 */
publicWidget.registry.ContactFormValidation = publicWidget.Widget.extend({
  selector: '#contactus_form',

  start: function () {
    var ret = this._super.apply(this, arguments);
    var submitBtn = this.el.querySelector('.o_website_form_send');
    if (submitBtn) {
      // Use capture phase (true) to intercept the click before Odoo's standard event handler
      submitBtn.addEventListener('click', this._onSubmit.bind(this), true);
    }
    return ret;
  },

  _onSubmit: function (ev) {
    var name = this.$('input[name="name"]');
    var email = this.$('input[name="email_from"]');
    var phone = this.$('input[name="phone"]');
    var $errorMsg = this.$('#contact_form_error');

    var valid = true;

    // Reset previous validation state
    name.removeClass('is-invalid');
    email.removeClass('is-invalid');
    phone.removeClass('is-invalid');
    $errorMsg.hide();

    if (!name.val().trim()) {
      valid = false;
      name.addClass('is-invalid');
    }

    if (!phone.val().trim()) {
      valid = false;
      phone.addClass('is-invalid');
    }

    if (!email.val().trim()) {
      valid = false;
      email.addClass('is-invalid');
    }

    if (!valid) {
      ev.preventDefault();
      ev.stopPropagation();
      ev.stopImmediatePropagation(); // Stop other listeners (Odoo submission) from running
      $errorMsg.show();
    }
  },
});

export default publicWidget.registry.ScrollAnimation;
