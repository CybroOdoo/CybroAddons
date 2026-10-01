###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amal George (odoo@cybrosys.com)
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
    'name': 'Fitness Center for Odoo Online',
    'version': '1.4',
    'category': 'Services',
    'summary': 'Manage fitness center operations, membership plans, schedules, and analytics.',
    'description': """
Fitness Center Management SaaS Module
=====================================
A comprehensive solution for managing gym and fitness center operations.

Key Features:
-------------
* **Membership Plans**: Configure custom membership levels, monthly fees, and durations.
* **Enrollments & Invoicing**: Streamline registrations, auto-calculate dates, and auto-generate invoices.
* **Class & Schedule Scheduling**: Manage fitness classes, trainers, capacities, and auto-generate daily training session calendars.
* **Automated Logic**: System constraints for check-ins/outs, enrollment sequence numbers, uniqueness, and capacity alerts.
* **Operations Dashboard**: Real-time analytical dashboard displaying active members, MRR, class occupancy, and upcoming expiries.
""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account',
                'hr',
                'maintenance',
                'web_studio'],
    'data': ['data/ir_model.xml',
             'data/ir_model_fields.xml',
             'data/ir_access.xml',
             'data/mail_template.xml',
             'data/ir_sequence.xml',
             'data/ir_actions_act_window.xml',
             'data/ir_actions_server.xml',
             'data/ir_dashboard.xml',
             'data/base_automation.xml',
             'data/ir_cron.xml',
             'data/ir_ui_view.xml',
             'data/ir_ui_menu.xml',
             'data/ir_default.xml'],
    'assets': {
        'web.assets_backend': [
            'fitness_center_saas/static/src/css/fitness_dashboard.css',
            'fitness_center_saas/static/src/xml/fitness_dashboard.xml',
            'fitness_center_saas/static/src/js/fitness_dashboard.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'application': True,
    'installable': True,
    'auto_install,': False
}
