# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "POS Claims",
    'version': '9.0.1.0.0',
    'summary': """Manage Customer Claims & Issues""",
    'description': """ This application allows to manage customers claims & issues in delivery.""",
    'category': 'Point of sale',
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'depends': ['base', 'point_of_sale'],
    'data': ['views/pos_claims_views.xml', 'views/pos_claims_popup.xml', 'views/pos_claim_sequence.xml'],
    'qweb': ['static/src/xml/pos_claim.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}