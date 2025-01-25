{
    "name": "Theme Diwy",
    "version": "18.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Diwy Backend Theme is an attractive theme for Odoo backend",
    "description": """Minimalist and elegant theme for Odoo backend""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web", "mail"],
    "data": [
    ],
    "assets": {
        "web.assets_backend": [
            "theme_diwy/static/src/xml/menu_panels.xml",
            "theme_diwy/static/src/xml/nav_bar_panel.xml",
            "theme_diwy/static/src/xml/home_menus.xml",
            "theme_diwy/static/src/xml/side_bar_panel.xml",
            "theme_diwy/static/src/scss/nav.scss",
            "theme_diwy/static/src/scss/sidebar.scss",
            "theme_diwy/static/src/css/style.css",
            "theme_diwy/static/src/js/home_menus.js",
            "theme_diwy/static/src/js/search_apps.js",
        ],
        "web.assets_frontend": [
            "theme_diwy/static/src/scss/login.scss",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
