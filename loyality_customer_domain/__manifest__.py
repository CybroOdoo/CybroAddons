# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Loyalty Customer Domain",
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Apply customer domain in Loyalty Programs',
    'description': """
                    This module extends the functionality of Loyalty Programs by allowing the application of 
                    customer-based domain filters in addition to product domains.

                    With this feature, loyalty programs can be configured to target specific customers or customer 
                    groups, enabling more precise and flexible promotional strategies.
                    
                    Key Features:
                    - Apply customer domain filters in Loyalty Programs
                    - Combine customer and product domains for advanced targeting
                    - Improve personalization of loyalty rewards and offers
                    - Seamless integration with existing Loyalty Program configurations
                    
                    This enhancement helps businesses create more targeted and effective loyalty campaigns.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_loyalty', 'sale_management'],
    'data': [
        'views/loyalty_rule_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
