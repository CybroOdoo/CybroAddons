# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Liquid Glass Backend Theme',
    'version': '17.0.1.0.0',
    'category': 'Theme/Backend',
    'summary': 'Modern, elegant glassmorphism backend theme for Odoo 17 Community Edition',
    'description': """
Liquid Glass Backend Theme for Odoo 17
======================================
Liquid Glass Backend Theme delivers a modern, elegant, and immersive glassmorphic interface
for Odoo 17 Community Edition. Crafted with translucent glass containers, frosted backgrounds,
subtle neon glow highlights, and refined typography.

Key Features:
-------------
* Ultra-modern Glassmorphic UI: Frosted glass panels with adaptive blur and depth effects.
* Refined Navigation: Floating translucent navbar with crystal-clear icons and quick access.
* Enhanced Forms & Lists: Polished input controls, glass sheets, and high-contrast typography.
* Dynamic Kanban & Card Layouts: Clean borders, smooth hover animations, and subtle shadows.
* Chart & Analytics Optimization: Automatic high-contrast label rendering for dark canvas views.
* Responsive & Lightweight: Fully optimized SCSS architecture with zero bloated dependencies.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'backend_theme_liquid_glass/static/src/scss/variables.scss',
            'backend_theme_liquid_glass/static/src/scss/buttons.scss',
            'backend_theme_liquid_glass/static/src/scss/forms.scss',
            'backend_theme_liquid_glass/static/src/scss/lists.scss',
            'backend_theme_liquid_glass/static/src/scss/kanban.scss',
            'backend_theme_liquid_glass/static/src/scss/modals.scss',
            'backend_theme_liquid_glass/static/src/scss/navbar.scss',
            'backend_theme_liquid_glass/static/src/scss/glass_theme.scss',
        ],
        'web.assets_backend_lazy': [
            'backend_theme_liquid_glass/static/src/js/canvas_text.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
