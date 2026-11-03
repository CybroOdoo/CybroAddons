# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# pylint: disable=manifest-required-author,manifest-deprecated-key
{
    'name': 'Survey Scheduler',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': (
        'Schedule surveys to automatically send invitation emails to '
        'participants'
    ),
    'description': (
        'With the help of this module, the user can schedule the survey '
        'and select the participants, and the survey is automatically sent '
        'to all selected participants.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['survey'],
    'data': [
        'data/ir_cron_data.xml',
        'views/survey_survey_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
