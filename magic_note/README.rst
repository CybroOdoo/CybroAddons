Magic Note for Odoo10 Notes
==========================

This module aims to automatically update the color of the notes/memo
in organizer tab under messaging menu.

Features
========

* set a name for the category of coloured notes
* Select color from a pre defined list of colors
* Select a range of date limit(days) in integer form
* Updates the note's color in on-load of kanban view


  .. note::

      By default on installation of this module it creates
      a field called dead date and sets it to the current date

    A new tab is created under settings-configuration where
    >set default color when no date intervals are defined
    >set color when any record doesn't come under date intervals
    >set color for notes which exceed the deadline date

  |formview|

* select a name which is not compulsory set lower and upper limit of days
* Select the color

  |listview|
* shows you the defied color and days(interval)

Credits
=======

Developer: Rahul @ cybrosys
Ported to v10: Jesni @ cybrosys
Guidance: Nilmar Shereef @ cybrosys, shereef@cybrosys.in
