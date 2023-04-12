/* ========================================================================
 * Bootstrap: dropdownhover.js v1.1.0
 * http://kybarg.github.io/bootstrap-dropdown-hover/
 * ========================================================================
 * Licensed under MIT (https://github.com/kybarg/bootstrap-dropdown-hover/blob/master/LICENSE)
 * ======================================================================== */


+function ($) {
  'use strict';

  // DROPDOWN CLASS DEFINITION
  // =========================

  var backdrop = '.dropdown-backdrop'

  var Dropdownhover = function (element, options) {
    this.options = options
    this.$element = $(element)

    var that = this

    // Defining if navigation tree or single dropdown
    this.dropdowns = this.$element.hasClass('dropdown-toggle') ? this.$element.parent().find('.dropdown-menu').parent('.dropdown') : this.$element.find('.dropdown')

    if (!options.onClick) {
      this.dropdowns.each(function () {
        $(this).on('mouseenter.bs.dropdownhover', function (e) {
          that.show($(this).children('a, button'))
        })
      })

      this.dropdowns.each(function () {
        $(this).on('mouseleave.bs.dropdownhover', function (e) {
          that.hide($(this).children('a, button'))
        })
      })
    } else {
      this.dropdowns.each(function () {
        $(this).children('a, button').on('click.bs.dropdownhover', function (e) {
          var isActive = $(this).parent().hasClass('open')
          isActive ? that.hide($(this)) : that.show($(this))
        })
      })
    }

  }

  Dropdownhover.TRANSITION_DURATION = 300
  Dropdownhover.DELAY = 150
  Dropdownhover.TIMEOUT

  Dropdownhover.DEFAULTS = {
    onClick: false,
    animations: ['fadeInDown', 'fadeInRight', 'fadeInUp', 'fadeInLeft'],
  }

  function getParent($this) {
    var selector = $this.attr('data-target')

    if (!selector) {
      selector = $this.attr('href')
      selector = selector && /#[A-Za-z]/.test(selector) && selector.replace(/.*(?=#[^\s]*$)/, '') // strip for ie7
    }

    var $parent = selector && $(document).find(selector)

    return $parent && $parent.length ? $parent : $this.parent()
  }

  function clearMenus(e) {
    if (e && e.which === 3) return
    $(backdrop).remove()
    $('[data-hover="dropdown"]').each(function () {
      var $this = $(this)
      var $parent = getParent($this)
      var relatedTarget = { relatedTarget: this }

      if (!$parent.hasClass('open')) return

      if (e && e.type == 'click' && /input|textarea/i.test(e.target.tagName) && $.contains($parent[0], e.target)) return

      $parent.trigger(e = $.Event('hide.bs.dropdownhover', relatedTarget))

      if (e.isDefaultPrevented()) return

      $this.attr('aria-expanded', 'false')
      $parent.removeClass('open').trigger($.Event('hidden.bs.dropdownhover', relatedTarget))
    })
  }

  // Opens dropdown menu when mouse is over the trigger element
  Dropdownhover.prototype.show = function (_dropdownLink) {
    var $this = $(_dropdownLink)


    window.clearTimeout(Dropdownhover.TIMEOUT)
    // Close all dropdowns
    $('.dropdown').not($this.parents()).each(function () {
      $(this).removeClass('open')
    });

    var effect = this.options.animations[0]

    if ($this.is('.disabled, :disabled')) return

    var $parent = $this.parent()
    var isActive = $parent.hasClass('open')

    if (!isActive) {

      if ('ontouchstart' in document.documentElement && !$parent.closest('.navbar-nav').length) {
        // if mobile we use a backdrop because click events don't delegate
        $(document.createElement('div'))
          .addClass('dropdown-backdrop')
          .insertAfter($(this))
          .on('click', clearMenus)
      }

      var $dropdown = $this.next('.dropdown-menu')

      $parent.addClass('open')
      $this.attr('aria-expanded', true)

      // Ensures that all menus that are closed have proper aria tagging.
      $parent.siblings().each(function () {
        if (!$(this).hasClass('open')) {
          $(this).find('[data-hover="dropdown"]').attr('aria-expanded', false);
        }
      })

      var side = this.position($dropdown)

      switch (side) {
        case 'top':
          effect = this.options.animations[2]
          break;
        case 'right':
          effect = this.options.animations[3]
          break;
        case 'left':
          effect = this.options.animations[1]
          break;
        default:
          effect = this.options.animations[0]
          break;
      }

      $dropdown.addClass('animated ' + effect)

      var transition = $.support.transition && $dropdown.hasClass('animated')

      transition ?
        $dropdown
          .one('bsTransitionEnd', function () {
            $dropdown.removeClass('animated ' + effect)
          })
          .emulateTransitionEnd(Dropdownhover.TRANSITION_DURATION) :
        $dropdown.removeClass('animated ' + effect)
    }

    return false
  }

  // Closes dropdown menu when mouse is out of it
  Dropdownhover.prototype.hide = function (_dropdownLink) {

    var that = this
    var $this = $(_dropdownLink)
    var $parent = $this.parent()
    var $this_delay = $this.data('dropdown-hover-delay');
    Dropdownhover.TIMEOUT = window.setTimeout(function () {
      $parent.removeClass('open')
      $this.attr('aria-expanded', false)
    }, ($this_delay ? $this_delay : Dropdownhover.DELAY))
  }

  // Calculating position of dropdown menu
  Dropdownhover.prototype.position = function (dropdown) {

    var win = $(window);

    // Reset css to prevent incorrect position
    dropdown.css({ bottom: '', left: '', top: '', right: '' }).removeClass('dropdownhover-top')

    var viewport = {
      top: win.scrollTop(),
      left: win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    viewport.bottom = viewport.top + win.height();

    var bounds = dropdown.offset();
    bounds.right = bounds.left + dropdown.outerWidth();
    bounds.bottom = bounds.top + dropdown.outerHeight();
    var position = dropdown.position();
    position.right = bounds.left + dropdown.outerWidth();
    position.bottom = bounds.top + dropdown.outerHeight();

    var side = ''

    var isSubnow = dropdown.parents('.dropdown-menu').length

    if (isSubnow) {

      if (position.left < 0) {
        side = 'left'
        dropdown.removeClass('dropdownhover-right').addClass('dropdownhover-left')
      } else {
        side = 'right'
        dropdown.addClass('dropdownhover-right').removeClass('dropdownhover-left')
      }

      if (bounds.left < viewport.left) {
        side = 'right'
        dropdown.css({ left: '100%', right: 'auto' }).addClass('dropdownhover-right').removeClass('dropdownhover-left')
      } else if (bounds.right > viewport.right) {
        side = 'left'
        dropdown.css({ left: 'auto', right: '100%' }).removeClass('dropdownhover-right').addClass('dropdownhover-left')
      }

      if (bounds.bottom > viewport.bottom) {
        dropdown.css({ bottom: 'auto', top: -(bounds.bottom - viewport.bottom) })
      } else if (bounds.top < viewport.top) {
        dropdown.css({ bottom: -(viewport.top - bounds.top), top: 'auto' })
      }

    } else { // Defines special position styles for root dropdown menu

      var parentLi = dropdown.parent('.dropdown')
      var pBounds = parentLi.offset()
      pBounds.right = pBounds.left + parentLi.outerWidth()
      pBounds.bottom = pBounds.top + parentLi.outerHeight()

      if (bounds.right > viewport.right) {
        dropdown.css({ left: -(bounds.right - viewport.right), right: 'auto' })
      }

      if (bounds.bottom > viewport.bottom && (pBounds.top - viewport.top) > (viewport.bottom - pBounds.bottom) || dropdown.position().top < 0) {
        side = 'top'
        dropdown.css({ bottom: '100%', top: 'auto' }).addClass('dropdownhover-top').removeClass('dropdownhover-bottom')
      } else {
        side = 'bottom'
        dropdown.addClass('dropdownhover-bottom')
      }
    }

    return side;

  }


  // DROPDOWNHOVER PLUGIN DEFINITION
  // ==========================

  function Plugin(option) {
    return this.each(function () {
      var $this = $(this)
      var data = $this.data('bs.dropdownhover')
      var settings = $this.data()
      if ($this.data('animations') !== undefined && $this.data('animations') !== null)
        settings.animations = $.isArray(settings.animations) ? settings.animations : settings.animations.split(' ')

      var options = $.extend({}, Dropdownhover.DEFAULTS, settings, typeof option == 'object' && option)

      if (!data) $this.data('bs.dropdownhover', (data = new Dropdownhover(this, options)))

    })
  }

  var old = $.fn.dropdownhover

  $.fn.dropdownhover = Plugin
  $.fn.dropdownhover.Constructor = Dropdownhover


  // DROPDOWNHOVER NO CONFLICT
  // ====================

  $.fn.dropdownhover.noConflict = function () {
    $.fn.dropdownhover = old
    return this
  }


  // APPLY TO STANDARD DROPDOWNHOVER ELEMENTS
  // ===================================
  $(document).ready(function () {
    $('[data-hover="dropdown"]').each(function () {
      var $target = $(this)
      if ('ontouchstart' in document.documentElement) {
        Plugin.call($target, $.extend({}, $target.data(), { onClick: true }))
      } else {
        Plugin.call($target, $target.data())
      }
    })
  })

}(jQuery);
