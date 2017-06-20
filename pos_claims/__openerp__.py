# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
    'summary': """Manage your customer claims""",
    'description': """ This application allows you to manage your customers claims.""",
    'category': 'Point of sale',
    'author': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
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