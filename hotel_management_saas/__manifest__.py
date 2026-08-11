###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeraj M (odoo@cybrosys.com)
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
    'name': 'Hotel Management for Odoo Online',
    'version': '1.4',
    'category': 'Industries',
    'summary': 'Hotel for Odoo Online, Hotel Management for Odoo Online, Odoo Online Custom Module, Hotel SaaS',
    'description': """Hotel Management for Odoo Online SaaS19.4, module featuring a unified dashboard,'
                   ' booking pipelines, automatically generated sequences, '
                   'customer invoicing, room maintenance tracking,'
                   ' guest folios, and automated checkout email notifications.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base',
                'hr',
                'account',
                'base_automation',
                'web_studio'],
    'data': ['data/ir_model.xml',
             'data/ir_model_fields.xml',
             'data/ir_sequence.xml',
             'data/ir_actions_act_window.xml',
             'data/ir_actions_report.xml',
             'data/mail_template.xml',
             'data/ir_actions_server.xml',
             'data/ir_ui_menu.xml',
             'data/base_automation.xml',
             'data/ir_access.xml',
             'data/ir_default.xml',
             'data/ir_ui_view.xml'],
    'demo': ['demo/hr_department.xml',
             'demo/mail_activity_type.xml',
             'demo/mail_activity.xml',
             'demo/x_booking_stage.xml',
             'demo/x_folios_stage.xml',
             'demo/x_maintance_stage.xml',
             'demo/x_room_stage.xml'],
    'assets': {
        'web.assets_backend': [
            'hotel_management_saas/static/src/js/hotel_dashboard.js',
            'hotel_management_saas/static/src/xml/hotel_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'application': True,
    'installable': True,
}
