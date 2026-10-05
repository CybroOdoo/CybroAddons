###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'IT Hardware Sales & Services',
    'version': '1.4',
    'category': 'Services',
    'summary': 'A comprehensive solution for managing IT Hardware Sales and Services in Odoo.',
    'description': """The IT Hardware Sales & Services module is designed to streamline operations 
    for IT hardware businesses. It manages sales, services, hardware
    configurations, and customer support efficiently within Odoo.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': [
        'account_reports',
        'crm',
        'helpdesk',
        'hr',
        'mail',
        'product',
        'project',
        'purchase',
        'repair',
        'sale',
        'stock',
        'web_studio',
        'website_sale',
    ],
    'data': [
        'data/ir_sequence.xml',
        'data/ir_model.xml',
        'data/ir_model_fields.xml',
        'data/ir_access.xml',
        'data/ir_actions_act_window.xml',
        'data/ir_ui_view.xml',
        'data/ir_ui_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'it_hardware_saas/static/src/dashboard/it_hardware_dashboard.scss',
            'it_hardware_saas/static/src/dashboard/it_hardware_dashboard.js',
            'it_hardware_saas/static/src/dashboard/it_hardware_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'application': True,
    'installable': True,
    'auto_install': False
}
