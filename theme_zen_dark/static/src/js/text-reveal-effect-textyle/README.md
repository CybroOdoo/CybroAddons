![enter image description here](https://user-images.githubusercontent.com/38127448/50680443-11477c80-104b-11e9-88a8-ec95cccd62af.gif)

# Textyle.js

A simple text effect with jQuery and tiny CSS.

# How to use

## JS

Textyle.js requires **jQuery** and **textyle.js** ( or **textyle.min.js**).  
Easing pattern can be extended by **jquery.easing.js**.

### read

	<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
	<script src="textyle.min.js"></script>
	
### call ( most simply )

	$('target').textyle();

## CSS

 ### target element

 opacity: 0;

### span (as child element)

 - **translate effect**
		position: relative;
		top: xxx;
		left: xxx;
    	
 - **fade effect**
		opacity: 0;

### example
    target {
    	opacity: 0;
    }
    target span {
    	/* translate effect */
    	position: relative;
    	top: 10px;
    	left: 10px;
    	/* fade effect */
    	opacity: 0;
    }

## Opitions

You can choose some following options or add callback function.  
Values below is default.

	$('target').textyle({
		duration : 400,
		delay : 100,
		easing : 'swing',
		callback : null
	});

Easing property can be extended by **jquery.easing.js**.  
If you want , add reading script below next to jQuery.

	<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js"></script>


### example

    $('target').textyle({
    	duration : 600,
    	delay : 150,
    	easing : 'linear',
    	callback : function(){
	   		$(this).css({
	   		color :  'coral',
	   		transition :  '1s',
	   		});
    	}
    });

# DEMO

 [codepen](https://codepen.io/mycreatesite/pen/vvpmgy)