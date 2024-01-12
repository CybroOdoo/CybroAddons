var mammoth = require("mammoth");
var pdf = require('html-pdf');

function convertToPdf(inputDocFilePathWithFileName, outputDocFilePathWithFileName, callback) {
  mammoth.convertToHtml({
      path: inputDocFilePathWithFileName
    })
    .then(function (result) {
      var html = result.value; // The generated HTML 
      pdf.create(html).toFile(outputDocFilePathWithFileName, function (err, res) {
        if (err) {
          callback(err);
          console.log(err);
          return;
        }
        callback(null, res);
      });
      var messages = result.messages; // Any messages, such as warnings during conversion 
      console.log(messages);
    })
    .done();
}

module.exports = convertToPdf;