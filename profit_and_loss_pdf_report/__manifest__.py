# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
{
    "name": "Profit And Loss PDF Report",
    "version": "15.0.1.0.0",
    "category": "Accounting",
    "summary": """Profit and Loss PDF Report in community""",
    "description": "This app, designed for use within the community edition"
                   "offers a valuable solution for businesses and individuals"
                   "seeking to efficiently generate and print profit and loss"
                   "reports in PDF format.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "http://www.cybrosys.com",
    "depends": ["account", "sale", "account_check_printing",
                "base_account_budget", "analytic"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/profit_loss_report_views.xml",
        "report/profit_loss_pdf_templates.xml",
        "report/profit_loss_pdf_reports.xml",
    ],
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
