# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWIN A K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Sales Incentives',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "This module will calculate incentive for each salesperson"
               " based on sale target in gamification",
    'description': "This module will calculate incentive for salesperson in "
                   "gamification,incentive version 17,"
                   "salesman,extra salary,salesman commision,"
                   " sale target,sale achievement,gamification,challenge,"
                   " crm,incentive,goal achievement,goal,extra pay,"
                   "sales target, rewards,target complete,employee,extra work,"
                   " work salary, achievement",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['sale', 'crm', 'gamification', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_incentive_views.xml',
        'views/incentive_approve_views.xml',
        'views/goal_views.xml',
        'views/gamification_challenge_views.xml',
        'report/incentive_report.xml',
        'views/calculate_incentive_views.xml',
        'views/sales_incentive_calculation_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 79,
    'currency': 'EUR',
}
