/* =========================================================
   CORDAGE THEME — Theme toggle, Navbar, Search, FAQ, Quote
   Works with Odoo 18's website frontend.
   ========================================================= */

(function () {
    'use strict';

    /* ── 1. Dark / Light theme toggle ──
       Uses Odoo's native color_scheme cookie and data-bs-theme.
    ── */
    /**
     * Synchronizes the theme toggle icon (sun/moon) based on the current mode.
     * @param {boolean} isLight - True if the theme is in light mode, false for dark mode.
     */
    function syncThemeIcon(isLight) {
        document.querySelectorAll('.cordage-theme-icon').forEach(function (svg) {
            svg.innerHTML = isLight
                /* Sun icon — shown in light mode */
                ? '<circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
                /* Moon icon — shown in dark mode */
                : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
        });
    }

    /**
     * Toggles the website theme between light and dark mode.
     * Updates native Odoo/Bootstrap attributes and cookies to persist the choice.
     */
    function toggleCordageTheme() {
        var html = document.documentElement;
        var isLight = html.classList.toggle('cordage-light');
        var themeValue = isLight ? 'light' : 'dark';

        // Native Odoo / Bootstrap 5.3 color scheme
        html.setAttribute('data-bs-theme', themeValue);
        document.cookie = "color_scheme=" + themeValue + "; path=/; max-age=31536000";
        localStorage.setItem('cordage-theme', themeValue);

        syncThemeIcon(isLight);
    }

    /* ── 2. Navbar: transparent → solid on scroll ── */
    /**
     * Initializes the transparent-to-solid navigation bar scroll effect
     * and handles mobile navigation toggles.
     */
    function initNavbar() {
        var nav = document.getElementById('bniNav');
        if (!nav) return;

        nav.classList.remove('bni-nav--solid');

        window.addEventListener('scroll', function () {
            nav.classList.toggle('bni-nav--solid', window.scrollY > 30);
        }, { passive: true });

        /* Mobile nav toggle */
        var toggle = document.getElementById('navToggle');
        var links = document.querySelector('.bni-nav__links');
        if (toggle && links) {
            toggle.addEventListener('click', function (e) {
                e.stopPropagation();
                links.classList.toggle('nav-open');
            });
            links.addEventListener('click', function (e) {
                if (e.target.tagName === 'A') links.classList.remove('nav-open');
            });
            document.addEventListener('click', function (e) {
                if (!links.contains(e.target) && !toggle.contains(e.target)) {
                    links.classList.remove('nav-open');
                }
            });
        }
    }

    /* ── 3. Search overlay ── */
    /**
     * Initializes the search overlay functionality and autocomplete demo grid.
     */
    function initSearch() {
        var overlay = document.getElementById('searchOverlay');
        var input = document.getElementById('searchInput');
        var closeBtn = document.getElementById('searchClose');
        var openBtn = document.getElementById('bniSearchBtn');

        if (!overlay) return;

        function openSearch() {
            overlay.classList.add('open');
            input && setTimeout(function () { input.focus(); }, 80);
        }
        function closeSearch() {
            overlay.classList.remove('open');
        }

        openBtn && openBtn.addEventListener('click', openSearch);
        closeBtn && closeBtn.addEventListener('click', closeSearch);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeSearch();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeSearch();
        });

        if (input) {
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var q = input.value.trim();
                    if (q) {
                        window.location.href = '/cordage-shop?search=' + encodeURIComponent(q);
                    }
                }
            });

            if (typeof PRODUCTS !== 'undefined') {
                input.addEventListener('input', function () {
                    var q = input.value.toLowerCase().trim();
                    var res = document.getElementById('searchResults');
                    if (!res) return;

                    if (!q) {
                        res.innerHTML = '';
                        return;
                    }
                    var hits = PRODUCTS.filter(function (p) {
                        return p.name.toLowerCase().includes(q) ||
                            (p.tags || []).join(' ').toLowerCase().includes(q);
                    }).slice(0, 6);

                    if (!hits.length) {
                        res.innerHTML = '<div class="sr-empty"><p>No results for <strong>' + q + '</strong></p><p style="font-size:12px;color:var(--b-muted-fg);margin-top:0.5rem">Press Enter to search full catalog</p></div>';
                        return;
                    }
                    res.innerHTML = '<div class="sr-count">Found <strong>' + hits.length + '</strong> demo product(s). <span style="font-size:12px;color:var(--b-muted-fg);">Press Enter to search full catalog.</span></div>' +
                        hits.map(function (p) {
                            return '<div class="sr-item" onclick="location.href=\'/cordage-shop?search=' + encodeURIComponent(p.name) + '\'">' +
                                '<div class="sr-item__img ' + (p.ropeClass || '') + '"></div>' +
                                '<div class="sr-item__info">' +
                                '<div class="sr-item__cat">' + (p.cat || '') + '</div>' +
                                '<div class="sr-item__name">' + p.name + '</div>' +
                                '<div class="sr-item__tags">' + (p.tags || []).map(function (t) {
                                    return '<span>' + t + '</span>';
                                }).join('') + '</div>' +
                                '</div>' +
                                '<div class="sr-item__price"><span>$' + p.price.toFixed(2) + '</span><small>' + (p.unit || '') + '</small></div>' +
                                '</div>';
                        }).join('');
                });
            }
        }
    }

    /* ── 4. Demo product grid (rendered when no Odoo products) ── */
    function initDemoProducts() {
        var grid = document.getElementById('productGrid');
        if (!grid) return;

        // Only run if we are in demo mode (indicated by the presence of #demoShopData)
        if (!document.getElementById('demoShopData')) return;

        if (typeof PRODUCTS === 'undefined' || typeof CATEGORIES === 'undefined') return;

        var PROD_IMGS = {
            p1: '/theme_cordage/static/src/images/img3.jpg',
            p2: '/theme_cordage/static/src/images/img6.webp',
            p3: '/theme_cordage/static/src/images/img1.jpg',
            p4: '/theme_cordage/static/src/images/img4.jpg',
            p5: '/theme_cordage/static/src/images/img5.webp',
            p6: '/theme_cordage/static/src/images/img2.jpg',
            p7: '/theme_cordage/static/src/images/img7.webp',
            p8: '/theme_cordage/static/src/images/img8.webp',
            p9: '/theme_cordage/static/src/images/img9.webp',
            p10: '/theme_cordage/static/src/images/img1.jpg',
            p11: '/theme_cordage/static/src/images/img4.jpg',
            p12: '/theme_cordage/static/src/images/img7.webp',
        };

        var MATERIALS = ['Natural Manila Fibre', 'Polypropylene (PP)', 'Steel core', 'Polyester', 'Nylon (Polyamide)', '100% Natural Cotton', 'Dyed Cotton', 'Nylon kernmantle'];
        var DIAMETERS = ['4 mm', '6 mm', '8 mm', '9.8 mm', '10 mm', '11 mm', '12 mm', '14 mm', '16 mm'];
        var activeCat = 'all', sortBy = 'featured', priceMin = 0, priceMax = 999;
        var activeMats = new Set(), activeDias = new Set();

        function catName(id) { return (CATEGORIES.find(function (c) { return c.id === id; }) || {}).name || id; }

        function buildSidebar() {
            var cats = [{ id: 'all', name: 'All Ropes' }].concat(CATEGORIES);
            var catFilterList = document.getElementById('catFilterList');
            if (catFilterList) {
                catFilterList.innerHTML = cats.map(function (c) {
                    return '<li><label><input type="radio" name="sidecat" value="' + c.id + '" ' + (c.id === activeCat ? 'checked' : '') + ' onchange="window.demoActiveCat=this.value;window.demoBuildChips();window.demoRenderGrid()"> ' + c.name + '</label></li>';
                }).join('');
            }
            var matList = document.getElementById('matList');
            if (matList) {
                matList.innerHTML = MATERIALS.map(function (m) {
                    return '<li><label><input type="checkbox" class="mat-cb" value="' + m + '"> ' + m + '</label></li>';
                }).join('');
            }
            var diaList = document.getElementById('diaList');
            if (diaList) {
                diaList.innerHTML = DIAMETERS.map(function (d) {
                    return '<li><label><input type="checkbox" class="dia-cb" value="' + d + '"> ' + d + '</label></li>';
                }).join('');
            }
        }

        function buildChips() {
            var chips = [{ id: 'all', name: 'All' }].concat(CATEGORIES);
            var chipsContainer = document.getElementById('chips');
            if (chipsContainer) {
                chipsContainer.innerHTML = chips.map(function (c) {
                    return '<button class="bni-tab ' + (c.id === activeCat ? 'active' : '') + '" onclick="window.demoActiveCat=\'' + c.id + '\';window.demoBuildChips();window.demoBuildSidebar();window.demoRenderGrid()">' + c.name + '</button>';
                }).join('');
            }
        }

        function renderGrid() {
            var list = PRODUCTS.filter(function (p) { return activeCat === 'all' || p.cat === activeCat; })
                .filter(function (p) { return p.price >= priceMin && p.price <= priceMax; });

            if (activeMats.size > 0) {
                list = list.filter(function (p) {
                    return Object.values(p.specs).some(function (v) { return activeMats.has(v); });
                });
            }
            if (activeDias.size > 0) {
                list = list.filter(function (p) { return activeDias.has(p.specs['Diameter']); });
            }

            switch (sortBy) {
                case 'price-asc': list.sort(function (a, b) { return a.price - b.price; }); break;
                case 'price-desc': list.sort(function (a, b) { return b.price - a.price; }); break;
                case 'name': list.sort(function (a, b) { return a.name.localeCompare(b.name); }); break;
            }

            var resCount = document.getElementById('resultCount');
            if (resCount) resCount.textContent = list.length + ' product' + (list.length !== 1 ? 's' : '');

            var empty = document.getElementById('emptyState');
            if (empty) empty.hidden = list.length > 0;

            grid.innerHTML = list.map(function (p) {
                return '<article class="bni-pcard">' +
                    '<a href="/cordage-product?id=' + p.id + '" style="display:block;text-decoration:none">' +
                    '<div class="bni-pcard__media ' + (p.ropeClass || '') + '">' +
                    '<img class="bni-pcard__photo" src="' + (PROD_IMGS[p.id] || '') + '" alt="' + p.name + '" loading="lazy" onerror="this.style.display=\'none\'"/>' +
                    (p.badge ? '<span class="bni-pcard__badge">' + p.badge + '</span>' : '') +
                    '</div>' +
                    '</a>' +
                    '<div class="bni-pcard__body">' +
                    '<div class="bni-pcard__cat">' + catName(p.cat) + '</div>' +
                    '<a href="/cordage-product?id=' + p.id + '" class="bni-pcard__name">' + p.name + '</a>' +
                    '<div class="bni-pcard__specs">' + p.tags.map(function (t) { return '<span class="bni-pcard__spec-pill">' + t + '</span>'; }).join('') + '</div>' +
                    '<div class="bni-pcard__rating"><span>' + '★'.repeat(Math.round(p.rating)) + '</span> ' + p.rating.toFixed(1) + ' · ' + p.reviews + ' reviews</div>' +
                    '<div class="bni-pcard__foot">' +
                    '<span class="bni-pcard__price">$' + p.price.toFixed(2) + '<span class="bni-pcard__unit">' + p.unit + '</span></span>' +
                    '<button class="bni-pcard__add" onclick="window.addToCart && window.addToCart(\'' + p.id + '\')">Add to Cart</button>' +
                    '</div>' +
                    '</div>' +
                    '</article>';
            }).join('');
        }

        // Expose globally for inline onclicks
        window.demoActiveCat = activeCat;
        window.demoBuildChips = function () { activeCat = window.demoActiveCat; buildChips(); };
        window.demoBuildSidebar = function () { activeCat = window.demoActiveCat; buildSidebar(); };
        window.demoRenderGrid = function () { activeCat = window.demoActiveCat; renderGrid(); };

        buildSidebar();
        buildChips();
        renderGrid();

        var sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', function (e) { sortBy = e.target.value; renderGrid(); });
        }
        var applyFilters = document.getElementById('applyFilters');
        if (applyFilters) {
            applyFilters.addEventListener('click', function () {
                var pMin = document.getElementById('priceMin');
                var pMax = document.getElementById('priceMax');
                priceMin = pMin && pMin.value ? +pMin.value : 0;
                priceMax = pMax && pMax.value ? +pMax.value : 999;

                activeMats.clear();
                document.querySelectorAll('.mat-cb').forEach(function (cb) { if (cb.checked) activeMats.add(cb.value); });

                activeDias.clear();
                document.querySelectorAll('.dia-cb').forEach(function (cb) { if (cb.checked) activeDias.add(cb.value); });

                renderGrid();
            });
        }
        var clearFilters = document.getElementById('clearFilters');
        if (clearFilters) {
            clearFilters.addEventListener('click', function () {
                priceMin = 0; priceMax = 999; activeMats.clear(); activeDias.clear();
                document.querySelectorAll('.mat-cb, .dia-cb').forEach(function (cb) { cb.checked = false; });
                var pMin = document.getElementById('priceMin');
                if (pMin) pMin.value = '';
                var pMax = document.getElementById('priceMax');
                if (pMax) pMax.value = '';
                renderGrid();
            });
        }
    }

    /**
     * Initializes the category tab filters for the product grid.
     * Works with both live Odoo products and demo products.
     */
    function initTabFilters() {
        var tabs = document.getElementById('cordageProdTabs');
        if (!tabs) return;

        tabs.addEventListener('click', function (e) {
            var tab = e.target.closest('[data-cat]');
            if (!tab) return;
            var activeCat = tab.dataset.cat;

            document.querySelectorAll('.bni-tab').forEach(function (t) {
                t.classList.remove('active');
            });
            tab.classList.add('active');

            var grid = document.getElementById('productGrid');
            if (!grid) return;

            // If we have demo products
            if (typeof window.renderDemoGrid === 'function' && (!grid.children.length || grid.querySelector('a[href="/shop"]'))) {
                window.renderDemoGrid(activeCat);
            } else {
                // Real products
                var cards = grid.querySelectorAll('.bni-pcard');
                cards.forEach(function (card) {
                    var cardCats = card.getAttribute('data-cat') || '';
                    if (activeCat === 'all' || cardCats.indexOf(activeCat) !== -1) {
                        card.style.display = '';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        });
    }

    /* ── 5. FAQ accordion ── */
    /**
     * Initializes the FAQ accordion logic for smooth expanding/collapsing.
     */
    function initFaq() {
        document.querySelectorAll('.ct-faq-q').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var answer = btn.nextElementSibling;
                var isOpen = btn.classList.contains('open');
                document.querySelectorAll('.ct-faq-q').forEach(function (b) {
                    b.classList.remove('open');
                    if (b.nextElementSibling) b.nextElementSibling.classList.remove('open');
                });
                if (!isOpen) {
                    btn.classList.add('open');
                    if (answer) answer.classList.add('open');
                }
            });
        });
    }

    /* ── 6. Quote form (AJAX — prevent full page reload) ── */
    /**
     * Initializes the quote request form with AJAX submission to prevent page reloads.
     */
    function initQuoteForm() {
        var form = document.getElementById('cordageQuoteForm');
        var msg = document.getElementById('cordageQuoteMsg');
        if (!form || !msg) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = form.querySelector('button[type=submit]');
            if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

            var data = new FormData(form);
            fetch(form.action, { method: 'POST', body: data, redirect: 'follow' })
                .then(function () {
                    msg.textContent = '✓ Request received — we\'ll reply within one business day.';
                    form.reset();
                })
                .catch(function () {
                    msg.style.color = '#e05555';
                    msg.textContent = 'Something went wrong. Please email us directly.';
                })
                .finally(function () {
                    if (btn) { btn.disabled = false; btn.textContent = 'Send Request'; }
                });
        });
    }

    /* ── DOM Ready ── */
    /**
     * Master initialization function. Triggers all DOM manipulation logic 
     * when the document is fully ready.
     */
    function init() {
        /* Theme toggle sync */
        var match = document.cookie.match(new RegExp('(^| )color_scheme=([^;]+)'));
        var t = match ? match[2] : localStorage.getItem('cordage-theme');
        var isLight = (t === 'light');

        if (isLight) {
            document.documentElement.classList.add('cordage-light');
            document.documentElement.setAttribute('data-bs-theme', 'light');
        } else {
            document.documentElement.classList.remove('cordage-light');
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        }

        syncThemeIcon(isLight);
        var toggleBtn = document.getElementById('cordageThemeToggle');
        if (toggleBtn) toggleBtn.addEventListener('click', toggleCordageTheme);

        initNavbar();
        initSearch();
        initDemoProducts();
        initTabFilters();
        initFaq();
        initQuoteForm();

        /* Year in footer */
        var yearEl = document.getElementById('cordageYear');
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
