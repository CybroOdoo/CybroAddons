/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.OdoNovaTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    events: {
        'click .odonova-pw-toggle, .password-toggle': '_onPasswordToggle',
        'click a[href^="#"]': '_onAnchorClick',
        'input .odonova-form-group input, .odonova-form-group textarea': '_onFormInput',
        'submit form': '_onFormSubmit',
    },

    /**
     * @override
     */
    start() {
        const def = this._super.apply(this, arguments);
        
        // Run initializations
        this._initStickyHeader();
        this._initScrollReveal();
        this._initCounters();
        this._initMobileNav();
        this._initActiveNav();
        this._initOdoNovaLogo();

        return def;
    },

    /**
     * @override
     */
    destroy() {
        this._super.apply(this, arguments);
        if (this._onScrollHandler) {
            window.removeEventListener('scroll', this._onScrollHandler);
        }
        if (this._onActiveNavScrollHandler) {
            window.removeEventListener('scroll', this._onActiveNavScrollHandler);
        }
    },

    /** ── 1. Scroll-aware header ─────────────────────────────────────────── */
    _initStickyHeader() {
        const header = this.el.querySelector('[data-odonova-header], .odonova-header');
        if (!header) return;

        const SCROLL_THRESHOLD = 20;

        this._onScrollHandler = () => {
            if (window.scrollY > SCROLL_THRESHOLD) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        };

        window.addEventListener('scroll', this._onScrollHandler, { passive: true });
        this._onScrollHandler(); // Trigger once on load
    },

    /** ── 2. Scroll-reveal via IntersectionObserver ──────────────────────── */
    _initScrollReveal() {
        const targets = this.el.querySelectorAll('.animate-on-scroll');
        if (!targets.length) return;

        if (!('IntersectionObserver' in window)) {
            targets.forEach(el => el.classList.add('visible'));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.12,
                rootMargin: '0px 0px -40px 0px',
            }
        );

        targets.forEach(el => observer.observe(el));
    },

    /** ── 3. Animated number counters ────────────────────────────────────── */
    _animateCounter(el) {
        const target = parseInt(el.dataset.target, 10);
        if (isNaN(target)) return;

        const duration = 1800; // ms
        const startTime = performance.now();
        const startValue = 0;

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // Ease-out cubic
            const current = Math.round(startValue + (target - startValue) * eased);
            
            el.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = target;
            }
        };

        requestAnimationFrame(update);
    },

    _initCounters() {
        const counters = this.el.querySelectorAll('.odonova-stat-number[data-target]');
        if (!counters.length) return;

        if (!('IntersectionObserver' in window)) {
            counters.forEach(el => this._animateCounter(el));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this._animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );

        counters.forEach(el => observer.observe(el));
    },

    /** ── 4. Mobile navigation toggle ────────────────────────────────────── */
    _initMobileNav() {
        if (this.editableMode) return; // Do not destroy Odoo editor DOM

        const odooOffcanvas = this.el.querySelector('#top_menu_collapse_mobile');
        if (!odooOffcanvas) return;

        const offcanvasBody = odooOffcanvas.querySelector('.offcanvas-body');
        if (offcanvasBody && !offcanvasBody.querySelector('.odonova-mobile-nav-list')) {
            offcanvasBody.innerHTML = `
                <ul class="odonova-mobile-nav-list">
                    <li><a href="/">Home</a></li>
                    <li><a href="/#s_odonova_services">Services</a></li>
                    <li><a href="/industries">Industries</a></li>
                    <li><a href="/case-studies">Case Studies</a></li>
                    <li><a href="/about_us">About</a></li>
                    <li><a href="/contactus" class="odonova-book-cta">Book Consultation</a></li>
                    <li><a href="/web/session/logout" class="odonova-book-cta">Logout</a></li>
                </ul>
            `;
        }

        const offcanvasHeader = odooOffcanvas.querySelector('.offcanvas-header');
        if (offcanvasHeader) offcanvasHeader.style.display = 'none';

        if (!odooOffcanvas.querySelector('.odonova-mobile-logo')) {
            const logoDiv = document.createElement('div');
            logoDiv.className = 'odonova-mobile-logo d-flex align-items-center gap-2 mb-4';
            logoDiv.innerHTML = `
                <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
                    <rect width="28" height="28" rx="5" fill="#0b66ff"/>
                    <path d="M7 9h5v10H7V9zm9 3h5v7h-5v-7z" fill="#fff"/>
                </svg>
                <span class="odonova-logo-text fs-5 fw-bold">OdoNova</span>
            `;
            odooOffcanvas.insertBefore(logoDiv, odooOffcanvas.firstChild);
        }
    },

    /** ── 5. Active nav link highlighting ────────────────────────────────── */
    _initActiveNav() {
        const navLinks = this.el.querySelectorAll('.odonova-navbar .nav-link, .nav a');
        if (!navLinks.length) return;

        const currentPath = window.location.pathname;

        // Path-based active state
        navLinks.forEach(link => {
            const href = link.getAttribute('href') || '';
            const linkPath = href.split('#')[0];

            if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) {
                link.classList.add('active');
            }
        });

        // Scroll-based active state for anchor links
        const sections = this.el.querySelectorAll('section[id]');
        if (!sections.length) return;

        this._onActiveNavScrollHandler = () => {
            let current = '';
            const headerHeight = this.el.querySelector('.odonova-header, .header')?.offsetHeight || 72;

            sections.forEach(section => {
                const sectionTop = section.offsetTop - headerHeight - 60;
                if (window.scrollY >= sectionTop) {
                    current = section.getAttribute('id');
                }
            });

            navLinks.forEach(link => {
                const href = link.getAttribute('href') || '';
                const linkPath = href.split('#')[0];
                if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) return;

                link.classList.remove('active');
                if (href === `#${current}` || href.endsWith(`#${current}`)) {
                    link.classList.add('active');
                }
            });
        };

        window.addEventListener('scroll', this._onActiveNavScrollHandler, { passive: true });
        this._onActiveNavScrollHandler();
    },

    /** ── 6. OdoNova Logo Injection ──────────────────────────────────────── */
    _initOdoNovaLogo() {
        if (this.editableMode) return; // Do not destroy Odoo editor DOM

        const isOdoNovaTheme = this.el.querySelector('[data-odonova-header]');
        if (!isOdoNovaTheme) return;

        const logoHTML = `
            <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
                <rect width="28" height="28" rx="5" fill="#0b66ff"/>
                <path d="M7 9h5v10H7V9zm9 3h5v7h-5v-7z" fill="#fff"/>
            </svg>
            <span class="odonova-logo-text fs-5 fw-bold">OdoNova</span>
        `;

        this.el.querySelectorAll('.navbar-brand').forEach(brand => {
            brand.innerHTML = logoHTML;
        });
    },

    /** ── Event Handlers ─────────────────────────────────────────────────── */
    _onPasswordToggle(ev) {
        const btn = ev.currentTarget;
        const wrapper = btn.closest('.odonova-pw-wrap, .password-wrapper');
        if (!wrapper) return;
        
        const input = wrapper.querySelector('input[type="password"], input[type="text"]');
        if (!input) return;

        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';

        btn.classList.toggle('is-visible', isPassword);
        btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    },

    _onAnchorClick(ev) {
        const link = ev.currentTarget;
        const isOdoNovaTheme = this.el.querySelector('[data-odonova-header]');
        
        const href = link.getAttribute('href');
        if (!href || href.indexOf('#') === -1) return;

        const targetId = href.substring(href.indexOf('#') + 1);
        if (!targetId) return;

        let target = document.getElementById(targetId);
        if (!target && isOdoNovaTheme) {
            target = this.el.querySelector(`.${targetId}, [data-snippet="${targetId}"], .s_odonova_${targetId}`);
        }

        if (target) {
            ev.preventDefault();
            const headerHeight = this.el.querySelector('.odonova-header, .header')?.offsetHeight || 72;
            const top = target.getBoundingClientRect().top + window.scrollY - headerHeight - 16;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    },

    _onFormInput(ev) {
        const input = ev.currentTarget;
        const label = input.closest('.odonova-form-group')?.querySelector('label');
        if (label) {
            label.classList.toggle('has-value', input.value.length > 0);
        }
    },

    _onFormSubmit(ev) {
        const btn = ev.currentTarget.querySelector('.odonova-btn-submit, .odonova-btn-login-submit');
        if (btn) {
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.textContent = 'Sending…';
            
            // Safety net to re-enable
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = originalText;
            }, 5000);
        }
    }
});

export default publicWidget.registry.OdoNovaTheme;
