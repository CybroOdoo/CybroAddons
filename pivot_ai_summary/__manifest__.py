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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "Pivot AI Summary",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "summary": "Generate instant summaries of complex pivot tables and interact with data using natural language queries.",
    'description': """An AI-powered chat assistant that delivers real-time
    summaries and interactive analysis of Pivot views. It enables users to
    ask natural language questions and instantly uncover meaningful business
    trends and insights from complex datasets. Fully integrated with the
    internal Liaison Guide (OLG), it provides a secure, keyless, and
    reliable AI experience.""",
    "author": "Cybrosys Techno Solutions",
    "company": 'Cybrosys Techno Solutions',
    "maintainer": 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "depends": ["web", "iap"],
    'external_dependencies': {
        'python': ['requests'],
    },
    "data": [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'pivot_ai_summary/static/src/js/pivot_summary_button.js',
            'pivot_ai_summary/static/src/xml/pivot_summary_button.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
