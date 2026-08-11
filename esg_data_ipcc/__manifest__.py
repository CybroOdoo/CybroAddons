# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##############################################################################
{
    "name": "ESG Data — IPCC EFDB",
    "version": "19.0.1.0.1",
    "summary": "IPCC EFDB provider for ESG data sources: direct emission factor import.",
    "description": """
        Adds IPCC EFDB as a provider in the ESG Data Sources framework.
        Downloads the IPCC EFDB XLS export and upserts data into enviro.emission.factor.

        Two actions on the Data Source form:
        - Import IPCC Factors: creates new records, skips existing ones.
        - Update IPCC Factors: creates new, updates existing, archives removed.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "category": "Sustainability",
    "depends": ["esg_data"],
    "data": [
        "data/enviro_data_source_data.xml",
        "views/enviro_data_source_views.xml",
        "views/enviro_emission_factor_views.xml",
    ],
    "external_dependencies": {
        "python": ["requests", "openpyxl"],
    },
    'images': ['static/description/banner.jpg'],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    'auto_install': False,
}
