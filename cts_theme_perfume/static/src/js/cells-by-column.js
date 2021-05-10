/*!
 * cellsByColumn layout mode for Isotope
 * v1.1.4
 * https://isotope.metafizzy.co/layout-modes/cellsbycolumn.html
 */

/*jshint browser: true, devel: false, strict: true, undef: true, unused: true */

( function( window, factory ) {
  // universal module definition
  /* jshint strict: false */ /*globals define, module, require */
  if ( typeof define === 'function' && define.amd ) {
    // AMD
    define( [
        'isotope-layout/js/layout-mode'
      ],
      factory );
  } else if ( typeof exports === 'object' ) {
    // CommonJS
    module.exports = factory(
      require('isotope-layout/js/layout-mode')
    );
  } else {
    // browser global
    factory(
      window.Isotope.LayoutMode
    );
  }

}( window, function factory( LayoutMode ) {
  'use strict';

  var CellsByColumn = LayoutMode.create( 'cellsByColumn' );
  var proto = CellsByColumn.prototype;

  proto._resetLayout = function() {
    // reset properties
    this.itemIndex = 0;
    // measurements
    this.getColumnWidth();
    this.getRowHeight();
    // set rows
    this.rows = Math.floor( this.isotope.size.innerHeight / this.rowHeight );
    this.rows = Math.max( this.rows, 1 );
  };

  proto._getItemLayoutPosition = function( item ) {
    item.getSize();
    var col = Math.floor( this.itemIndex / this.rows );
    var row = this.itemIndex % this.rows;
    // center item within cell
    var x = ( col + 0.5 ) * this.columnWidth - item.size.outerWidth / 2;
    var y = ( row + 0.5 ) * this.rowHeight - item.size.outerHeight / 2;
    this.itemIndex++;
    return { x: x, y: y };
  };

  proto._getContainerSize = function() {
    return {
      width: Math.ceil( this.itemIndex / this.rows ) * this.columnWidth
    };
  };

  proto.needsResizeLayout = function() {
    return this.needsVerticalResizeLayout();
  };

  return CellsByColumn;

}));
