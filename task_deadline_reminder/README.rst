Task DeadLine Reminder v14
==========================
This module extends the functionality of project module to allow to send  deadline reminder emails on task deadline day.

Configuration
=============

By default, a cron job named "Task DeadLine Reminder" will be created while installing this module.
This cron job can be found in:

	**Settings > Technical > Automation > Scheduled Actions**

This job runs daily by default.

Usage
=====

To use this functionality, you need to:

#. Create a project to which the new tasks will be related.
#. Add a name, deadline date, who the task will be assigned to, etc...
#. In order to send email reminder to responsible user,you have to set reminder box (Project > Task > Reminder )
#. Go to the Scheduled Action(Settings > Technical > Automation > Scheduled Action) and edit the time at which  Deadline Reminder Action is to be done

The cron job will do the rest.

Installation
============
- www.odoo.com/documentation/11.0/setup/install.html
- Install our custom addon

Bug Tracker
===========
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Credits
=======
Cybrosys Techno Solutions <www.cybrosys.com>

Author
------
*  Developer v9: Saritha @ cybrosys
*  Developer v10, v11: Niyas Raphy @ cybrosys
*                 V13: Nimisha
* Version 14: JIBIN JAMES Contact: odoo@cybrosys.com

Maintainer
----------

This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com.








