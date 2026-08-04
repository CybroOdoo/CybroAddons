# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "ESG Data Sources",
    "version": "19.0.1.0.0",
    "category": "Sustainability",
    "summary": "Base data source framework for ESG emission factor providers",
    "description": """
                    Provides the base enviro.data.source model for managing ESG emission factor data
                    providers and importers.
                    
                    - enviro.data.source: configurable provider records (one per data source)
                    - Provider pattern: add new sources as separate modules using selection_add
                    
                    Install provider modules (e.g. enviro_data_climatiq, esg_data_ipcc) on top of this.
                        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["esg_emission_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/enviro_data_source_views.xml",
        "views/enviro_data_menus.xml",
    ],
    "license": "LGPL-3",
    'images': ['static/description/banner.jpg'],
    "installable": True,
    'auto_install': False,
    "application": False,
}
