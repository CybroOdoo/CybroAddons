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
#############################################################################
{
    "name": "Profit And Loss PDF Report",
    "version": "20.0.1.0.0",
    "category": "Accounting",
    "summary": """Profit and Loss PDF Report in community""",
    "description": """This app, designed for use within the community edition,
     offers a valuable solution for businesses and individuals seeking to
     efficiently generate and print profit and loss reports in PDF format.""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["account"],
    "data": [
        "security/ir.access.csv",
        "wizard/profit_loss_report_views.xml",
        "report/profit_loss_pdf_templates.xml",
        "report/profit_loss_pdf_reports.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    'auto_install': False,
    'application': False,
}
