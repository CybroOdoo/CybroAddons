# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
{
    'name': 'Odoo Module Health Report',
    'version': '18.0.2.2.1',
    'category': 'Productivity',
    'summary': "Odoo Module Health Monitoring Tool",
    'description': 'Displays odoo apps report in the menu and as a PDF report.',
    'license': 'OPL-1',
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'depends': ['base', 'web'],
    'external_dependencies': {
        'python': [
            'isort',
            'black',
            'bandit',
            'radon',
            'pylint',
            'pylint-odoo',
            'flake8'
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'reports/ir_actions_report.xml',
        'reports/odoo_health_report.xml',
        'views/odoo_health_report_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js',
            'https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&family=Public+Sans:ital,wght@0,100..900;1,100..900&display=swap.css',
            'odoo_health_report/static/src/css/main.css',
            'odoo_health_report/static/src/js/module_quality.js',
            'odoo_health_report/static/src/js/health_dashboard.js',
            'odoo_health_report/static/src/js/dashboard_wrapper.js',
            'odoo_health_report/static/src/xml/module_quality.xml',
            'odoo_health_report/static/src/xml/health_dashboard.xml',
            'odoo_health_report/static/src/xml/dashboard_wrapper.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}
