# Timesheet Based Payroll

Payroll based on Timesheet hours. While computing payroll the approved total sheet hours submitted by
  employees are calculated. This addon creates a rule of category BASIC for hour based calculations. So while creating
  salary structure for timesheet based payroll we have to select the rule there.

  - Flag which enables the contract as timesheet based.
  - Flag which enables the salary structure for timesheet based.
  - Timesheet hours and total hours on payslip view.
  - Salary Rule for timesheet based calculations.


### Depends
Timesheet Based Payroll depends on hr, hr_timesheet_sheet, hr_timesheet_attendance,hr_payroll

### Tech

* [Python] - Models
* [XML] - Odoo views

### Installation
- www.odoo.com/documentation/10.0/setup/install.html
- Install our custom addon, which also installs its depends [hr, hr_payroll, hr_timesheet_sheet, hr_timesheet_attendance]
 
### Usage
> Enable Timesheet Based Payroll on contract.
> Enable Timesheet Based structure on salary structure.
> Select Hourly Pay (Timesheet) rule while creating salary structure.
> payslip will display total hours and total timesheet hours,
  if the employee contract is enabled Timesheet Based Payroll



License
----
GNU LESSER GENERAL PUBLIC LICENSE, Version 3 (LGPLv3)
(http://www.gnu.org/licenses/agpl.html)



