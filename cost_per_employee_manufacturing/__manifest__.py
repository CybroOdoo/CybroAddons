# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
###############################################################################
{
    "name": "Cost per Employees in Manufacturing",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "summary": """Calculate Cost per Employees in Manufacturing""",
    "description": """This module helps to Calculate Cost per Employees in 
     Manufacturing.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": [
        "base",
        "mrp",
        "hr",
        "account_accountant",
        "account",
        "mrp_subcontracting_account_enterprise",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_views.xml",
        "views/mrp_workcenter_views.xml",
        "views/mrp_production_views.xml",
        "views/cost_structure_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cost_per_employee_manufacturing/static/src/js/cost_per_employee.js"
        ]
    },
    "images": ["static/description/banner.jpg"],
    "license": "OPL-1",
    "installable": True,
    "auto_install": False,
    "application": False,
}
