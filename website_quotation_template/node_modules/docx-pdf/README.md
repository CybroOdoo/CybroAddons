Docx to pdf
=========

A library that converts docx file to pdf.

## Installation

  npm install docx-pdf --save

## Usage

    var docxConverter = require('docx-pdf');

    docxConverter('./input.docx','./output.pdf',function(err,result){
      if(err){
        console.log(err);
      }
      console.log('result'+result);
    });
    
    its basically docxConverter(inputPath,outPath,function(err,result){
      if(err){
        console.log(err);
      }
      console.log('result'+result);
    });
  
  Output should be output.pdf which will be produced on the output path your provided


## Contributing

This was created just for solo usage purpose. Anybody is welcome to contribute to it.
