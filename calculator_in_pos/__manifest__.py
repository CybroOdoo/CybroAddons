# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Calculator in POS Screen',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """A simple virtual calculator with option to enable/disable it
    from POS configuration.""",
    'description': """This module provides a straightforward virtual calculator
    in the POS, offering users the flexibility to enable or disable its 
    functionality through the POS configuration settings allowing users to
    effortlessly perform calculations within the POS environment.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': ['views/pos_config_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'calculator_in_pos/static/src/app/calculator_button/calculator_button.js',
            'calculator_in_pos/static/src/app/calculator_button/calculator_button.xml',
            'calculator_in_pos/static/src/app/calculator_popup/calculator_popup.js',
            'calculator_in_pos/static/src/app/calculator_popup/calculator_popup.xml',
            'calculator_in_pos/static/src/css/calculator_in_pos.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'price': 4.99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
