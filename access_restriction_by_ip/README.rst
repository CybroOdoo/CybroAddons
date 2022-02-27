Access Restriction By IP V12
============================

This module will restrict users access to his account from the specified IP only. If user access his
account from  non-specified IP, login will be restricted and a warning message will be displayed in
login page.

You can also enter a ip address V4 or V6 with subnet like 192.168.1.1/24 or 2001:db8::/64.

If no IP is specified for a user, then there will not be restriction by IP. He can access from any IP.

Requires python ipaddress module. install by
pip install ipaddress

Credits
=======
Cybrosys Techno Solutions

Authors
-------
* Niyas Raphy <odoo@cybrosys.com>
* Ahmet Altinisik <aaltinisik@altinkaya.com.tr>