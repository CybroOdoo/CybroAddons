# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectConfiguration(models.TransientModel):
    _name = 'hr.config.settings'
    _inherit = 'res.config.settings'

    module_hr_custody = fields.Boolean(
        string='Custody Management',
        help='Helps you to manage Custody Requests.\n'
             '- This installs the module Custody Management.')
    module_employee_check_list = fields.Boolean(
        string='Employee Checklist',
        help='Helps you to manage Employee Checklist.\n'
             '- This installs the module Employee Checklist.')
    module_hr_employee_shift = fields.Boolean(
        string='Employee Shift',
        help='Helps you to manage Employee Shift.\n'
             '- This installs the module Employee Shift.')
    module_hr_employee_transfer = fields.Boolean(
        string='Employee Transfer',
        help='Helps you to manage Employee Transfer.\n'
             '- This installs the module Employee Transfer.')
    module_hr_insurance = fields.Boolean(
        string='Employee Insurance',
        help='Helps you to manage Employee Insurance.\n'
             '- This installs the module Employee Insurance.')
    module_hr_lawsuit_management = fields.Boolean(
        string='Lawsuit Management',
        help='Helps you to manage Lawsuit Management.\n'
             '- This installs the module Lawsuit Management.')
    module_hr_payslip_monthly_report = fields.Boolean(
        string='Payroll-Payslip Reporting',
        help='Helps you to manage Payroll-Payslip Reporting.\n'
             '- This installs the module Payroll-Payslip Reporting.')
    module_hr_recruitment_validations = fields.Boolean(
        string='Advanced HR Recruitment',
        help='Helps you to manage Advanced HR Recruitment.\n'
             '- This installs the module Advanced HR Recruitment.')
    module_hr_resignation = fields.Boolean(
        string='Resignation Process',
        help='Helps you to manage Resignation Process.\n'
             '- This installs the module Resignation Process.')
    module_hr_vacation_mngmt = fields.Boolean(
        string='Vacation Management',
        help='Helps you to manage Vacation Management.\n'
             '- This installs the module Vacation Management.')
    module_hr_zk_attendance = fields.Boolean(
        string='Biometric Device Integration',
        help='Helps you to manage Biometric Device Integration.\n'
             '- This installs the module Biometric Device Integration.')

