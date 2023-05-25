# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3 (AGPL v3)
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
    'name': 'Vehicle Inspection Management in Fleet',
    'version': '16.0.1.0.0',
    'category': 'Industries',
    'summary': 'Vehicle Inspection Management for manage the Vehicle '
               'Inspection and services',
    'description': 'Vehicle Inspection Management used to manage the Fleet '
                   'Inspection and Services',
    'depends': ['base', 'fleet'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'data': {
        'security/vehicle_inspection_access.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/vehicle_inspection_views.xml',
        'views/inspection_request_views.xml',
        'wizards/fleet_service_inspection_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_vehicle_log_services_views.xml',
        'views/vehicle_service_log_views.xml',
        'reports/vehicle_inspection_reports.xml',
        'reports/vehicle_inspection_report_templates.xml',
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
