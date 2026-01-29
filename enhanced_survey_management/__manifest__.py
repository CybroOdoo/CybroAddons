# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V   (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 OPL-1)
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
###############################################################################
{
    'name': 'Enhanced Survey Management',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Enhance your survey management with new question kinds and more',
    'description': 'Upgrade your survey management capabilities with the '
                   'addition of versatile question types. '
                   'Capture specific timeframes by incorporating questions '
                   'about the month, week, or range, '
                   'enabling finer data analysis. '
                   'Furthermore, enhance data collection by allowing '
                   'respondents to upload files, '
                   'fostering a more comprehensive understanding of their '
                   'experiences.'
                   'Explore these new question types and optimize your survey '
                   'strategy for enhanced insights.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['survey', 'website'],
    'data': [
        'data/enhanced_survey_management_data.xml',
        'security/ir.model.access.csv',
        'views/survey_templates.xml',
        'views/survey_question_views.xml',
        'views/survey_input_print_templates.xml',
        'views/survey_portal_templates.xml',
        'views/survey_user_views.xml',
        'views/survey_survey_views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css',
            'https://cdn.jsdelivr.net/npm/flatpickr@4.6.3/dist/flatpickr.min.js',
            'enhanced_survey_management/static/src/js/survey_form.js',
            'enhanced_survey_management/static/src/js/survey_submit.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
