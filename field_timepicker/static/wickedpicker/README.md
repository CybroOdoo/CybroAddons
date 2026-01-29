# Wickedpicker

## wickedpicker.js - A simple jQuery timepicker

## Requirements

* [jQuery](http://jquery.com/download/) (>= 1.9)

## Installation
```shell
    $ bower install wickedpicker
```

## Usage

#### In your HTML
 ```html
 <body>
 ....
 <input type="text" name="timepicker" class="timepicker"/>
 ....
 <script type="text/javascript" src="jquery-1.11.3.min.js"></script>
  <script type="text/javascript" src="wickedpicker.js"></script>
 </body>
 ```

#### In your JavaScript file
 ```javascript
     $('.timepicker').wickedpicker();
 ```

#### Options
```javascript
    var options = {
        now: "12:35", //hh:mm 24 hour format only, defaults to current time
        twentyFour: false,  //Display 24 hour format, defaults to false
        upArrow: 'wickedpicker__controls__control-up',  //The up arrow class selector to use, for custom CSS
        downArrow: 'wickedpicker__controls__control-down', //The down arrow class selector to use, for custom CSS
        close: 'wickedpicker__close', //The close class selector to use, for custom CSS
        hoverState: 'hover-state', //The hover state class to use, for custom CSS
        title: 'Timepicker', //The Wickedpicker's title,
        showSeconds: false, //Whether or not to show seconds,
        timeSeparator: ' : ', // The string to put in between hours and minutes (and seconds)
        secondsInterval: 1, //Change interval for seconds, defaults to 1,
        minutesInterval: 1, //Change interval for minutes, defaults to 1
        beforeShow: null, //A function to be called before the Wickedpicker is shown
        afterShow: null, //A function to be called after the Wickedpicker is closed/hidden
        show: null, //A function to be called when the Wickedpicker is shown
        clearable: false, //Make the picker's input clearable (has clickable "x")
    };
    $('.timepicker').wickedpicker(options);
```

#### Methods

'time' get the current time inside of the input element that has a wickedpicker attached to it.
```javascript
    $('.timepicker').wickedpicker('time');
```

  If multiple input fields have the same class and instantiate a wickedpicker then pass the index of the timepicker
  you'd like to select
 ```javascript
    $('.timepicker').wickedpicker('time', 0);
 ```

#### Functionality
    The Wickedpicker opens when the bound input is clicked, or focused on (try tabbing), and it can be closed by either
    clicking the X, by clicking outside of it, or by pressing esc. The arrows icons increase or decrease their
    associated time values or toggle the meridiem.  The values can also be changed using the up and down keys when
    focused on. To move to the next value just press the left or right arrow key.

For more checkout
[Wickedpicker gh-pages](http://ericjgagnon.github.io/wickedpicker/)

## License

 Copyright (c) 2015-2016 Eric Gagnon Licensed under the MIT license.

