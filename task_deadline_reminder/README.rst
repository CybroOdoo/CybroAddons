Task DeadLine Reminder v10
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

Credits
=======
Cybrosys Techno Solutions <www.cybrosys.com>

Author
------
*  Developer v9: Saritha @ cybrosys
*  Developer v10: Niyas Raphy @ cybrosys









