/** @odoo-module **/

// Load Chart.js dynamically and safely
function loadChartJSAndInit() {
    try {
        if (typeof window.Chart === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = () => {
                try { initChart(); } catch (e) { console.error(e); }
            };
            document.head.appendChild(script);
        } else {
            initChart();
        }
    } catch (e) {
        console.error("Error loading Chart:", e);
    }
}

function startUp() {
    try {
        loadChartJSAndInit();
        initNav();
        initScrollReveal();
        initCounters();
        initCaseFilter();
        initBlogFilter();
    } catch (e) {
        console.error("Error initializing Converza JS:", e);
    }
}

// Execute safely, handling both sync and async Odoo module loading
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    startUp();
} else {
    document.addEventListener("DOMContentLoaded", startUp);
}

function initChart() {
    const revCanvas = document.getElementById("revenueChart");
    if (revCanvas) {
        new Chart(revCanvas, {
            type: "bar",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                datasets: [{
                    label: "Revenue",
                    data: [15, 22, 30, 38, 45, 60, 72, 84, 92, 108, 125, 140],
                    backgroundColor: "#1A5FB4",
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: "#cfd8dc" } },
                    y: { beginAtZero: true, ticks: { color: "#cfd8dc" }, grid: { color: "rgba(255,255,255,.08)" } }
                }
            }
        });
    }

    const trafficCanvas = document.getElementById("trafficChart");
    if (trafficCanvas) {
        new Chart(trafficCanvas, {
            type: "doughnut",
            data: {
                labels: ["Organic SEO", "Paid Search", "Social Media", "Email", "Direct"],
                datasets: [{
                    data: [38, 21, 16, 9, 16],
                    backgroundColor: ["#1677ff", "#12d0c4", "#8c63ff", "#f4b000", "#58637d"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                cutout: '70%',
                plugins: { legend: { display: false } }
            }
        });
    }

    const organicCanvas = document.getElementById("organicChart");
    if (organicCanvas) {
        new Chart(organicCanvas, {
            type: "line",
            data: {
                labels: ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"],
                datasets: [{
                    label: "Traffic",
                    data: [1000, 1800, 3200, 5000, 7500, 10000],
                    borderColor: "#0ed46d",
                    backgroundColor: "rgba(14, 212, 109, 0.1)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { display: false, beginAtZero: true }
                },
                elements: { point: { radius: 0 } }
            }
        });
    }
}

function initNav() {
    const nav = document.getElementById("nav");
    if (!nav) {
        return;
    }

    window.addEventListener(
        "scroll",
        () => {
            nav.classList.toggle("scrolled", window.scrollY > 40);
        },
        { passive: true }
    );
}

function initScrollReveal() {
    const io = new IntersectionObserver(
        (entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) {
                    e.target.classList.add("on");
                    io.unobserve(e.target);
                }
            });
        },
        {
            threshold: 0.1,
            rootMargin: "0px 0px -30px 0px",
        }
    );

    document.querySelectorAll(".rv:not(.show)").forEach((el) => {
        io.observe(el);
    });
}

function countUp(el) {
    const end = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || "";
    const isFloat = el.dataset.count.includes(".");
    const duration = 1800;
    const start = performance.now();

    function animate(now) {
        const progress = Math.min((now - start) / duration, 1);
        const value = end * (1 - Math.pow(1 - progress, 3));

        el.textContent =
            (isFloat ? value.toFixed(1) : Math.round(value)) + suffix;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

function initCounters() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) {
                    countUp(e.target);
                    observer.unobserve(e.target);
                }
            });
        },
        {
            threshold: 0.5,
        }
    );

    document.querySelectorAll("[data-count]").forEach((el) => {
        observer.observe(el);
    });
}

function initCaseFilter() {
    const filterBtns = document.querySelectorAll('.case-filter-btn');
    const caseCards = document.querySelectorAll('.case-card');

    if (!filterBtns.length || !caseCards.length) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Get target id (e.g. "#b2b" -> "b2b")
            // Handle absolute URLs that contain hashes
            const hrefUrl = this.getAttribute('href');
            let targetId = '';
            
            if (hrefUrl && hrefUrl.includes('#')) {
                 targetId = hrefUrl.split('#')[1];
            } else if (hrefUrl === '#') {
                 targetId = '';
            }

            // Filter cards
            caseCards.forEach(card => {
                if (targetId === '' || targetId === 'all') { // For "All Industries" (href="#")
                    card.style.display = 'block';
                } else {
                    if (card.id === targetId) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    });
}

function initBlogFilter() {
    const filterBtns = document.querySelectorAll('.filter-bar .filter-btn');
    const blogCards = document.querySelectorAll('.blog-grid .blog-card');

    if (!filterBtns.length || !blogCards.length) return;

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            const filterValue = this.getAttribute('data-filter');

            // Filter cards
            blogCards.forEach(card => {
                if (filterValue === 'all') {
                    card.style.display = 'block';
                } else {
                    if (card.getAttribute('data-category') === filterValue) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    });
}
