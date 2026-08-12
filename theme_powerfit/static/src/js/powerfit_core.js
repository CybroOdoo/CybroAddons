/** @odoo-module **/
/**
 * Powerfit Core Widget
 *
 * This widget is responsible for initializing and managing the core
 * functionality of the Powerfit theme, including cursor effects, navbar
 * behavior, and other interactive elements.
 */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PowerfitCore = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        this._initEditableRoot();
        this._initCursor();
        this._initNavbar();
        this._initMobileNav();
        this._initMenuOverflow();
        this._initAnimations();
        this._initCarousel();
        this._initLightbox();
        this._initMembershipPrefill();
        this._initDynamicContent();
        return this._super.apply(this, arguments);
    },

    _initEditableRoot: function () {
        // Only add o_editable to #wrap on the public-facing page (i.e. outside
        // the website builder editor). Inside the editor Odoo manages its own
        // editable-root registry; injecting o_editable after the editor has
        // bootstrapped produces orphaned parent references in MovePlugin,
        // causing "Cannot read properties of null (reading 'children')".
        if (document.body.classList.contains('editor_enable')) {
            return;
        }
        const wrap = document.getElementById('wrap');
        if (wrap) {
            wrap.classList.add('o_editable');
        }
    },

    _initCursor: function () {
        const dot = document.getElementById('cursorDot');
        const ring = document.getElementById('cursorRing');
        if (!dot || !ring) return;

        let mx = 0, my = 0, rx = 0, ry = 0;
        document.addEventListener('mousemove', (e) => {
            mx = e.clientX;
            my = e.clientY;
            dot.style.left = mx + 'px';
            dot.style.top = my + 'px';
        });

        const animRing = () => {
            rx += (mx - rx) * 0.12;
            ry += (my - ry) * 0.12;
            ring.style.left = rx + 'px';
            ring.style.top = ry + 'px';
            requestAnimationFrame(animRing);
        };
        animRing();

        document.querySelectorAll('a, button, .service-card, .trainer-card, .gallery-item').forEach(el => {
            el.addEventListener('mouseenter', () => { dot.classList.add('hovering'); ring.classList.add('hovering'); });
            el.addEventListener('mouseleave', () => { dot.classList.remove('hovering'); ring.classList.remove('hovering'); });
        });
    },

    _initNavbar: function () {
        const navbar = document.getElementById('navbar');
        const btt = document.getElementById('backToTop');

        // ── Backend bar offset ───────────────────────────────────────────────
        // When a user is logged in, Odoo renders a 46px backend toolbar
        // (.o_main_navbar) above #wrapwrap. Our navbar is position:fixed so it
        // must be pushed down by that bar's height, and the hero/banner padding
        // must grow by the same amount so content isn't hidden beneath it.
        const applyBackendOffset = () => {
            const backendBar = document.querySelector('.o_main_navbar');
            const offset = backendBar ? backendBar.offsetHeight : 0;
            if (navbar) {
                navbar.style.top = offset > 0 ? `${offset}px` : '';
            }
            // Push hero content down so it clears the (now lower) navbar
            const hero = document.querySelector('.hero > .container');
            if (hero) {
                hero.style.paddingTop = offset > 0 ? `${100 + offset}px` : '';
            }
            // Push page-banner sections (inner pages) down by the same offset
            const banner = document.querySelector('.page-banner');
            if (banner) {
                // page-banner already has var(--sp-20)=160px top padding — just add offset
                banner.style.paddingTop = offset > 0 ? `calc(var(--sp-20) + ${offset}px)` : '';
            }
        };
        applyBackendOffset();
        // Re-apply if the backend bar mounts late (e.g. website editor toolbar)
        window.addEventListener('resize', applyBackendOffset);

        // Highlight selected navbar menu item matching current page path
        const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
        document.querySelectorAll('.nav-links a, .mobile-nav a').forEach(link => {
            const href = link.getAttribute('href');
            if (href) {
                const linkPath = href.replace(/\/$/, '') || '/';
                if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            }
        });

        // Make Back to Top button functional
        if (btt) {
            btt.addEventListener('click', (e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        const handleScroll = () => {
            const scrollY = window.scrollY || (document.getElementById('wrapwrap') ? document.getElementById('wrapwrap').scrollTop : 0);
            if (navbar) {
                if (scrollY > 60) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }
            if (btt) {
                if (scrollY > 400) {
                    btt.classList.add('visible');
                } else {
                    btt.classList.remove('visible');
                }
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        const wrapwrap = document.getElementById('wrapwrap');
        if (wrapwrap) {
            wrapwrap.addEventListener('scroll', handleScroll, { passive: true });
        }
    },

    _initMobileNav: function () {
        const hamburger = document.getElementById('hamburger');
        const mobileNav = document.getElementById('mobileNav');

        if (hamburger && mobileNav) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                mobileNav.classList.toggle('open');

                if (mobileNav.classList.contains('open')) {
                    mobileNav.scrollTop = 0;
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            });

            mobileNav.querySelectorAll('a').forEach(a => {
                a.addEventListener('click', () => {
                    hamburger.classList.remove('active');
                    mobileNav.classList.remove('open');
                    document.body.style.overflow = '';
                });
            });
            window.addEventListener('resize', () => {
                if (window.innerWidth > 768) {
                    hamburger.classList.remove('active');
                    mobileNav.classList.remove('open');
                    document.body.style.overflow = '';
                }
            });
        }
    },

    /**
     * Collapses desktop nav-links into a "+" dropdown when there are too
     * many top-level menu items to fit comfortably. Below the mobile
     * breakpoint (768px, matches style.scss) the hamburger already owns
     * the full menu, so this is skipped there.
     */
    _initMenuOverflow: function () {
        const navLinks = document.getElementById('navLinks');
        const navbar = document.getElementById('navbar');
        if (!navLinks || !navbar) return;

        const MOBILE_BREAKPOINT = 768; // keep in sync with style.scss
        const MAX_VISIBLE_ITEMS = 6;   // show the first 5 links, collapse the rest
        let moreBtn = null;      // <li class="menu-more"> toggle, lives inside #navLinks
        let moreDropdown = null; // <ul class="menu-more-dropdown">, lives outside #navLinks

        const restore = () => {
            if (!moreBtn) return;
            [...moreDropdown.children].forEach((li) => {
                navLinks.insertBefore(li, moreBtn);
            });
            moreBtn.remove();
            moreDropdown.remove();
            moreBtn = null;
            moreDropdown = null;
        };

        const positionDropdown = () => {
            // Positioned relative to the navbar (JS-computed) rather than
            // nested inside #navLinks, so it can't get clipped by anything.
            const navbarRect = navbar.getBoundingClientRect();
            const toggleRect = moreBtn.getBoundingClientRect();
            moreDropdown.style.top = `${toggleRect.bottom - navbarRect.top + 12}px`;
            moreDropdown.style.right = `${navbarRect.right - toggleRect.right}px`;
        };

        const buildMoreButton = () => {
            const li = document.createElement('li');
            li.className = 'menu-more';
            li.innerHTML =
                '<a href="#" class="menu-more-toggle" aria-haspopup="true" aria-expanded="false">' +
                '<iconify-icon icon="ph:plus-bold"></iconify-icon></a>';
            navLinks.appendChild(li);

            const dropdown = document.createElement('ul');
            dropdown.className = 'menu-more-dropdown';
            navbar.appendChild(dropdown); // outside #navLinks on purpose, see restore()/positionDropdown()

            const toggle = li.querySelector('.menu-more-toggle');
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const isOpen = li.classList.toggle('open');
                toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
                dropdown.classList.toggle('open', isOpen);
                if (isOpen) {
                    positionDropdown();
                }
            });

            moreBtn = li;
            moreDropdown = dropdown;
        };

        const adapt = () => {
            // Below the mobile breakpoint, the hamburger owns the full menu.
            if (window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches) {
                restore();
                return;
            }

            restore();

            // Only the real menu links count toward the limit — not a
            // "+" button from a previous run (already removed by restore()).
            const items = [...navLinks.children];
            if (items.length <= MAX_VISIBLE_ITEMS) {
                return; // fits within the limit, nothing to collapse
            }

            buildMoreButton();

            const overflowItems = items.slice(MAX_VISIBLE_ITEMS);
            overflowItems.forEach((li) => moreDropdown.appendChild(li));
        };

        document.addEventListener('click', (e) => {
            if (moreBtn && moreBtn.classList.contains('open')
                && !moreBtn.contains(e.target)
                && !(moreDropdown && moreDropdown.contains(e.target))) {
                moreBtn.classList.remove('open');
                moreBtn.querySelector('.menu-more-toggle').setAttribute('aria-expanded', 'false');
                moreDropdown.classList.remove('open');
            }
        });

        window.addEventListener('resize', () => {
            // Item count doesn't change with width, but we still need to
            // switch between "hamburger owns it" and "+ owns it" as the
            // viewport crosses the mobile breakpoint.
            adapt();
        });

        adapt();
    },

    _initAnimations: function () {
        /* ---- Scroll reveal + counters + progress bars ---- */
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });

        document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

        /* ---- Counter animation ---- */
        function animateCounter(el, target, suffix) {
            let start = 0;
            const duration = 2000;
            const step = (timestamp) => {
                if (!start) start = timestamp;
                const progress = Math.min((timestamp - start) / duration, 1);
                const ease = 1 - Math.pow(1 - progress, 3);
                const val = Math.floor(ease * target);
                el.textContent = val.toLocaleString() + (suffix || '+');
                if (progress < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        }

        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.dataset.count);
                    const suffix = el.dataset.suffix || '+';
                    animateCounter(el, target, suffix);
                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));

        const progressObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    setTimeout(() => { bar.style.width = bar.dataset.width + '%'; }, 200);
                    progressObserver.unobserve(bar);
                }
            });
        }, { threshold: 0.3 });

        document.querySelectorAll('.progress-bar-fill').forEach(el => progressObserver.observe(el));

        /* ---- Quote cascade ---- */
        const quotes = document.querySelectorAll('.quote-item');
        const quoteObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    quotes.forEach((q, i) => setTimeout(() => q.classList.add('visible'), i * 300));
                    quoteObserver.disconnect();
                }
            });
        }, { threshold: 0.2 });

        const quotesContainer = document.getElementById('quotesContainer');
        if (quotesContainer) quoteObserver.observe(quotesContainer);
    },

    _initCarousel: function () {
        /* ---- Carousel ---- */
        const track = document.getElementById('testimonialsTrack');
        const dotsWrap = document.getElementById('carouselDots');
        const cards = track ? track.querySelectorAll('.testimonial-card') : [];
        if (!track || cards.length === 0) return;

        let current = 0;

        function getPerPage() { return window.innerWidth <= 768 ? 1 : 2; }
        function getMaxIndex() { return Math.max(0, cards.length - getPerPage()); }

        function goTo(index) {
            const max = getMaxIndex();
            current = Math.max(0, Math.min(index, max));
            /* Use the actual rendered card width + CSS gap (--sp-4 = 32px) */
            const gap = 32;
            const cardWidth = cards[0] ? cards[0].getBoundingClientRect().width + gap : 0;
            track.style.transform = `translateX(-${current * cardWidth}px)`;
            document.querySelectorAll('.carousel-dot').forEach((d, i) => d.classList.toggle('active', i === current));
        }

        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        if (prevBtn) prevBtn.addEventListener('click', () => goTo(current - 1));
        if (nextBtn) nextBtn.addEventListener('click', () => goTo(current + 1));

        if (dotsWrap) {
            dotsWrap.querySelectorAll('.carousel-dot').forEach(d => {
                d.addEventListener('click', () => goTo(parseInt(d.dataset.index)));
            });
        }

        function nextSlide() { goTo(current >= getMaxIndex() ? 0 : current + 1); }
        let autoCarousel = setInterval(nextSlide, 5000);
        track.addEventListener('mouseenter', () => clearInterval(autoCarousel));
        track.addEventListener('mouseleave', () => { autoCarousel = setInterval(nextSlide, 5000); });
        window.addEventListener('resize', () => goTo(0));
    },

    _initLightbox: function () {
        /* ---- Gallery lightbox ---- */
        const lightbox = document.getElementById('lightbox');
        const lightboxImg = document.getElementById('lightboxImg');
        if (!lightbox || !lightboxImg) return;

        document.querySelectorAll('.gallery-item img').forEach(img => {
            img.addEventListener('click', () => {
                lightboxImg.src = img.src;
                lightboxImg.alt = img.alt;
                lightbox.classList.add('open');
                document.body.style.overflow = 'hidden';
            });
        });

        const lightboxClose = document.getElementById('lightboxClose');
        if (lightboxClose) {
            lightboxClose.addEventListener('click', () => {
                lightbox.classList.remove('open');
                document.body.style.overflow = '';
            });
        }

        lightbox.addEventListener('click', e => {
            if (e.target === lightbox) {
                lightbox.classList.remove('open');
                document.body.style.overflow = '';
            }
        });
    },

    _initMembershipPrefill: function () {
        /* ---- Membership plan enquiry prefill ---- *
         * When a visitor clicks "Get Started" on a membership card, they are
         * redirected to /contactus?plan=<tier>&product=<name>&price=<price>.
         */
        const params = new URLSearchParams(window.location.search);
        const plan = params.get('plan');
        const product = params.get('product');
        const price = params.get('price');

        if (!plan) return;   // Not arriving from a membership card — do nothing

        const form = document.querySelector('.s_website_form form');
        if (form) {
            // Add custom hidden field formatted exactly as requested
            const addHiddenField = (name, value) => {
                let input = document.createElement('input');
                input.type = 'hidden';
                input.name = name;
                input.value = value;
                input.classList.add('s_website_form_input');
                form.appendChild(input);
            };

            let planDetails = '\nSelected Gym Plan : ' + plan;
            if (price) planDetails += '\nPrice : $' + price + '/month';

            // This will render in CRM Notes as:
            // Gym Plan : 
            // Selected Gym Plan : Basic
            // Price : $20/month
            const boldLabel = '<span style="font-size: 18px; font-weight: bold;">Gym Plan</span>';
            addHiddenField(boldLabel, planDetails);
        }

        // Also prefill the subject field if it exists, to make it look nice for the user
        // Using a short timeout to ensure it overrides Odoo's session restore if needed
        setTimeout(() => {
            const subjectInput = document.getElementById('subject') || document.querySelector('input[name="subject"]');
            if (subjectInput && !subjectInput.value.trim()) {
                subjectInput.value = 'Enquiry for ' + plan + ' Plan';
            }
        }, 300);

        // Scroll the form into view
        setTimeout(() => {
            if (form) form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500);
    },

    _initDynamicContent: function () {
        // Never mutate the DOM while the website builder editor is active.
        // Replacing innerHTML inside an oe_structure container while the editor
        // is running orphans its internal node registry, causing MovePlugin to
        // crash with "Cannot read properties of null (reading 'children')" when
        // it tries to walk siblings for overlay-button visibility.
        if (document.body.classList.contains('editor_enable')) {
            return;
        }

        // Fetch trainers via RPC
        this._fetchTrainers();

        // Fetch membership plans via RPC
        this._fetchMembershipPlans();
    },

    _escapeHtml: function (str) {
        const div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    },

    _fetchTrainers: function () {
        const trainersGrid = document.getElementById('trainersGrid');
        if (!trainersGrid) return;

        fetch('/theme_powerfit/trainers/data')
            .then((response) => (response.ok ? response.json() : []))
            .then((trainers) => {
                // No backend trainers configured: keep the static demo
                // cards already present in the arch, do nothing.
                if (!trainers || !trainers.length) return;
                trainersGrid.innerHTML = trainers
                    .map((trainer, index) => this._renderTrainerCard(trainer, index))
                    .join('');
            })
            .catch(() => {
                // Network/server error: silently keep the static fallback.
            });
    },

    _renderTrainerCard: function (trainer, index) {
        const esc = this._escapeHtml.bind(this);
        const delayClass = 'reveal-delay-' + ((index % 3) + 1);
        const socials = [
            ['instagram', trainer.instagram, 'ph:instagram-logo-fill'],
            ['twitter', trainer.twitter, 'ph:twitter-logo-fill'],
            ['linkedin', trainer.linkedin, 'ph:linkedin-logo-fill'],
        ].filter(([, url]) => !!url).map(([label, url, icon]) => (
            `<a href="${esc(url)}" aria-label="${esc(label)}" target="_blank" rel="noopener noreferrer">` +
            `<iconify-icon icon="${icon}"></iconify-icon></a>`
        )).join('');

        const experience = trainer.experience ? `${trainer.experience}+` : '0';
        const clients = trainer.clients ? `${trainer.clients}+` : '0';
        const rating = trainer.rating ? `${Number(trainer.rating).toFixed(1)}★` : 'N/A';

        return `
            <div class="trainer-card reveal from-bottom ${delayClass}">
             <div class="trainer-img">
              <img src="${esc(trainer.image_url)}" alt="${esc(trainer.name)}"
                   onerror="this.src='/theme_powerfit/static/src/img/snippets/trainer_default.png'"/>
              <div class="trainer-overlay"></div>
              <div class="trainer-social">${socials}</div>
              <div class="trainer-info">
               <span class="trainer-tag">${esc(trainer.job || 'Personal Trainer')}</span>
               <h3 class="trainer-name">${esc(trainer.name)}</h3>
               <div class="trainer-details">
                <p class="trainer-bio">${esc(trainer.description)}</p>
                <div class="trainer-achievements">
                 <div class="trainer-ach"><div class="trainer-ach-num">${esc(experience)}</div><div class="trainer-ach-label">Years</div></div>
                 <div class="trainer-ach"><div class="trainer-ach-num">${esc(clients)}</div><div class="trainer-ach-label">Clients</div></div>
                 <div class="trainer-ach"><div class="trainer-ach-num">${esc(rating)}</div><div class="trainer-ach-label">Rating</div></div>
                </div>
               </div>
              </div>
             </div>
            </div>`;
    },

    _fetchMembershipPlans: function () {
        const pricingGrid = document.getElementById('pricingGrid');
        if (!pricingGrid) return;

        fetch('/theme_powerfit/membership/data')
            .then((response) => (response.ok ? response.json() : []))
            .then((plans) => {
                // No backend gym plans configured: keep the static demo
                // cards already present in the arch, do nothing.
                if (!plans || !plans.length) return;
                pricingGrid.innerHTML = plans
                    .map((plan, index) => this._renderPricingCard(plan, index))
                    .join('');
            })
            .catch(() => {
                // Network/server error: silently keep the static fallback.
            });
    },

    _renderPricingCard: function (plan, index) {
        const esc = this._escapeHtml.bind(this);
        const delayClass = 'reveal-delay-' + ((index % 3) + 1);
        const cardClass = plan.is_featured
            ? `pricing-card featured reveal from-bottom ${delayClass}`
            : `pricing-card reveal from-bottom ${delayClass}`;
        const ctaClass = plan.is_featured
            ? 'pricing-cta pricing-cta-filled'
            : 'pricing-cta pricing-cta-outline';
        const badge = plan.is_featured
            ? '<div class="pricing-popular-badge">Most Popular</div>' : '';

        const features = (plan.features && plan.features.length)
            ? plan.features.map((feat) => (
                `<li class="pricing-feature${feat.available ? '' : ' unavailable'}">` +
                `<iconify-icon icon="${feat.available ? 'ph:check-bold' : 'ph:x-bold'}"></iconify-icon> ` +
                `${esc(feat.text)}</li>`
            )).join('')
            : '<li class="pricing-feature"><iconify-icon icon="ph:check-bold"></iconify-icon> Full Gym Access</li>';

        return `
            <div class="${cardClass}">
             ${badge}
             <div class="pricing-plan-name">${esc(plan.label)}</div>
             <div class="pricing-price">
              <span class="pricing-currency">$</span>
              <span class="pricing-amount">${esc(plan.price)}</span>
              <span class="pricing-period">/month</span>
             </div>
             <p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:4px;">${esc(plan.description || '—')}</p>
             <div class="pricing-divider"></div>
             <ul class="pricing-features">${features}</ul>
             <a href="${esc(plan.contact_url)}" class="${ctaClass}">Get Started</a>
            </div>`;
    }
});
