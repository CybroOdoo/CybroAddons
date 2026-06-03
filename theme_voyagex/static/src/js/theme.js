/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Header "Get the App" Button: Injects the button via JS into the navbar.
 */
publicWidget.registry.VxHeaderGetApp = publicWidget.Widget.extend({
    selector: 'header .navbar',
    disabledInEditableMode: true,

    start: function () {
        this._injectBtn();
        return this._super.apply(this, arguments);
    },

    _injectBtn: function () {
        if (!this.el.querySelector('.vx-header-get-app')) {
            var container = this.el.querySelector('.container, .container-fluid');
            if (container) {
                var btn = document.createElement('a');
                btn.href = '/get-app';
                btn.className = 'vx-header-get-app';
                btn.textContent = 'Get the App';
                container.appendChild(btn);
            }
        }
    },

    destroy: function () {
        var btn = this.el.querySelector('.vx-header-get-app');
        if (btn) { btn.remove(); }
        this._super.apply(this, arguments);
    },
});

/**
 * Hero Phone Parallax: Subtle parallax effect on hero phones on scroll.
 */
publicWidget.registry.VxHeroPhones = publicWidget.Widget.extend({
    selector: '.s_vx_hero',
    disabledInEditableMode: true,

    start: function () {
        this._bindScroll();
        return this._super.apply(this, arguments);
    },

    _bindScroll: function () {
        var self = this;
        this._onScroll = function () {
            // Safety check for snippet preview mode
            if (!self.el || !document.body.contains(self.el) || self.el.closest('.oe_snippet, .o_we_snippet_preview, #oe_snippets')) return;
            
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            var phones = self.el.querySelector('.vx-hero-phones');
            if (phones && scrollTop < 800) {
                var offset = scrollTop * 0.08;
                phones.style.transform = 'translateY(' + offset + 'px)';
            }
        };
        window.addEventListener('scroll', this._onScroll, { passive: true });
    },

    destroy: function () {
        if (this._onScroll) {
            window.removeEventListener('scroll', this._onScroll);
        }
        this._super.apply(this, arguments);
    },
});

/**
 * Gallery Hover: Hover animations for the app gallery screens.
 */
publicWidget.registry.VxGalleryHover = publicWidget.Widget.extend({
    selector: '.s_vx_gallery',
    disabledInEditableMode: true,

    start: function () {
        this._initIntersectionObserver();
        return this._super.apply(this, arguments);
    },

    _initIntersectionObserver: function () {
        // Safety check for snippet sidebar and editor
        if (window.self !== window.top || window.location.pathname.indexOf('/snippets') !== -1) return;
        if (document.body && document.body.classList.contains('editor_enable')) return;
        if (this.el.closest('.oe_snippet, .o_we_snippet_preview, #oe_snippets')) return;
        
        var items = this.el.querySelectorAll('.vx-gallery-phone');
        if (!items.length) return;

        this._observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        items.forEach(function (item) {
            // item.style.opacity = '0';
            // item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            this._observer.observe(item);
        }.bind(this));
    },

    destroy: function () {
        if (this._observer) {
            this._observer.disconnect();
        }
        this._super.apply(this, arguments);
    },
});

/**
 * Screen Showcase 3D Tilt: Perspective tilt effect on card hover.
 */
publicWidget.registry.VxScreenShowcase = publicWidget.Widget.extend({
    selector: '.vx-screen-showcase-card',
    disabledInEditableMode: true,

    events: {
        'mousemove': '_onMouseMove',
        'mouseleave': '_onMouseLeave',
    },

    start: function () {
        this._phoneFrame = this.el.querySelector('.vx-phone-frame');
        return this._super.apply(this, arguments);
    },

    _onMouseMove: function (ev) {
        if (!this._phoneFrame) return;
        // Safety check for Odoo editor previews and snippet sidebar
        if (!this.el || !document.body.contains(this.el) || this.el.offsetParent === null) return;
        if (this.el.closest('.oe_snippet, .o_we_snippet_preview, #oe_snippets, .o_wysiwyg')) return;
        if (window.self !== window.top && document.body.classList.contains('editor_enable')) return;
        
        var rect;
        try {
            // Use native getBoundingClientRect to avoid Odoo's buggy oldGetBoundingClientRect recursion
            rect = Element.prototype.getBoundingClientRect.call(this.el);
        } catch (e) {
            return;
        }
        
        if (!rect || rect.width === 0) return;
        var x = ev.clientX - rect.left;
        var y = ev.clientY - rect.top;
        var centerX = rect.width / 2;
        var centerY = rect.height / 2;
        var rotateY = ((x - centerX) / centerX) * -5;
        var rotateX = ((y - centerY) / centerY) * 3;
        this._phoneFrame.style.transform =
            'rotateY(' + rotateY + 'deg) rotateX(' + rotateX + 'deg) scale(1.02)';
    },

    _onMouseLeave: function () {
        if (!this._phoneFrame) return;
        this._phoneFrame.style.transform = '';
    },

    destroy: function () {
        if (this._phoneFrame) {
            this._phoneFrame.style.transform = '';
        }
        this._super.apply(this, arguments);
    },
});

/**
 * Feature Section Fade In: Scroll-based fade-in animations for feature sections.
 */
publicWidget.registry.VxFadeInSection = publicWidget.Widget.extend({
    selector: '.s_vx_feature_left, .s_vx_feature_right, .s_vx_more_features',
    disabledInEditableMode: true,

    start: function () {
        this._initFadeIn();
        return this._super.apply(this, arguments);
    },

    _initFadeIn: function () {
        // Safety check for snippet sidebar and editor
        if (window.self !== window.top || window.location.pathname.indexOf('/snippets') !== -1) return;
        if (document.body && document.body.classList.contains('editor_enable')) return;
        if (this.el.closest('.oe_snippet, .o_we_snippet_preview, #oe_snippets')) return;

        // this.el.style.opacity = '0';
        // this.el.style.transform = 'translateY(30px)';
        this.el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';

        this._observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.15 });

        this._observer.observe(this.el);
    },

    destroy: function () {
        if (this._observer) {
            this._observer.disconnect();
        }
        this._super.apply(this, arguments);
    },
});

export default {
    VxHeaderGetApp: publicWidget.registry.VxHeaderGetApp,
    VxHeroPhones: publicWidget.registry.VxHeroPhones,
    VxGalleryHover: publicWidget.registry.VxGalleryHover,
    VxScreenShowcase: publicWidget.registry.VxScreenShowcase,
    VxFadeInSection: publicWidget.registry.VxFadeInSection,
};
