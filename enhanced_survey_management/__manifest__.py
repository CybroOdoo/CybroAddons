#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Enhanced Survey Management',
    'version': '20.0.1.0.0',
    'category': 'Marketing/Surveys',
    'summary': 'Enhance your survey management with custom question types, portal history, and XLSX reporting.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['portal', 'survey', 'website'],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
        'security/ir.access.csv',
        'data/enhanced_survey_management_data.xml',
        'views/survey_templates.xml',
        'views/survey_question_views.xml',
        'views/survey_input_print_templates.xml',
        'views/survey_portal_templates.xml',
        'views/survey_user_views.xml',
        'views/survey_survey_views.xml',
    ],
    'assets': {
        'survey.survey_assets': [
            'enhanced_survey_management/static/src/js/survey_form.js',
            'enhanced_survey_management/static/src/js/survey_submit.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
