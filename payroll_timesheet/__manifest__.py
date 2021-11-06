# -*- coding: utf-8 -*-
{
    'name': "TimeSheet Based Payroll",
    'version': "10.0.1.0.0",
    'summary': """
        Payrolls Are Computed According to the Submitted & Confirmed Timesheets By Employees.""",
    'description': """
        Payrolls are computed according to the submitted and confirmed Timesheets By employees.
    """,

    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'category': "Generic Modules/Human Resources",
    'depends': [
        "base",
        "hr_payroll",
        "hr_timesheet_sheet",
        "hr_timesheet_attendance",
    ],
    'data': [
        'data/data.xml',
        'views/views.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'application': True
}
