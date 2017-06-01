
POS Customer Pricelist v8
=========================

This module adds Pricelist to Point Of Sale Session.


* Use customer specific pricelist inside POS.
* Assign pricelist  while creating customer from POS.
* User can also change pricelist in POS Session.
* Unique Ticket Id is specified for each ticket.


Installation
============

No extra module is required,other than the depending module POS.

Usage
=====

To use this module, you need to:

* Go to Pont of sale main menu
* Select the Resume session/New session
* Click on 'Unknown customer'-->Edit/Create Customer, then Add pricelist for the customer


Implementation
==============

User can assign POS pricelist from POS session for each customer.
Then price value of all the products in POS will be changed according to the customer selected.
If no pricelist is set for the customer,module will select default pricelist.











