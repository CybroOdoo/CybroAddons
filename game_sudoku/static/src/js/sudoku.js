var maxAttempts=100;
var globb;
var check = 0
var selected_cell_id;
var current_cell = null;
var sudokuboard = new Array(9);
var orginalboard = new Array(9);
var board = new Array(9);
Puzzle=new Array(9);
maxAttempts=100;
var thisCol;
var thisRow;
var subMat;
var time=0;
var checkit=0;

odoo.define('game_sudoku.models_sudoku_game', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;

var Sudoku = Widget.extend({
    events: {
        "click .sudokunewbutton": function() {
            $('.sudokulevelselection').css('display', 'block');
        },
        "click .sudokulevelbutton1": function() {
            this.newgame();
            this.level(45);
            checkit = 1;
            $('.sudokulevelselection').css('display', 'none');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttoncheckback').css('display', 'none');
            $('.sudokulevelbuttonreset').css('display', 'block');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttonsolve').css('display', 'block');
        },
        "click .sudokulevelbutton2": function() {
            this.newgame();
            this.level(35);
            checkit = 1;
            $('.sudokulevelselection').css('display', 'none');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttoncheckback').css('display', 'none');
            $('.sudokulevelbuttonreset').css('display', 'block');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttonsolve').css('display', 'block');
        },
        "click .sudokulevelbutton3": function() {
            this.newgame();
            this.level(25);
            checkit = 1;
            $('.sudokulevelselection').css('display', 'none');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttoncheckback').css('display', 'none');
            $('.sudokulevelbuttonreset').css('display', 'block');
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttonsolve').css('display', 'block');
        },
        "click .sudokulevelselectionclose": function() {
            $('.sudokulevelselection').css('display', 'none');
        },
        "click .sudokulevelbuttonreset": function() {
            $('.sudokulevelbuttoncheck').css('display', 'block');
            $('.sudokulevelbuttoncheckback').css('display', 'none');
            this.rese();
        },
        "click .sudokulevelbuttoncheck": function() {
            this.check();
             $('.sudokulevelbuttoncheck').css('display', 'none');
             $('.sudokulevelbuttoncheckback').css('display', 'block');
        },
        "click .sudokulevelbuttoncheckback": function() {
            this.checkback();
             $('.sudokulevelbuttoncheck').css('display', 'block');
             $('.sudokulevelbuttoncheckback').css('display', 'none');
        },
        "click .sudokulevelbuttonsolve": function() {
            this.show_lost();
            this.solve();
        },
        "click #cell_0_0": function() {
        var cell = document.getElementById('cell_0_0');
        var cell_id = "#cell_0_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_1": function() {

        var cell = document.getElementById('cell_0_1');
        var cell_id = "#cell_0_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_2": function() {

        var cell = document.getElementById('cell_0_2');
        var cell_id = "#cell_0_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_3": function() {

        var cell = document.getElementById('cell_0_3');
        var cell_id = "#cell_0_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_4": function() {

        var cell = document.getElementById('cell_0_4');
        var cell_id = "#cell_0_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_5": function() {

        var cell = document.getElementById('cell_0_5');
        var cell_id = "#cell_0_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_6": function() {

        var cell = document.getElementById('cell_0_6');
        var cell_id = "#cell_0_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_7": function() {

        var cell = document.getElementById('cell_0_7');
        var cell_id = "#cell_0_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_0_8": function() {

        var cell = document.getElementById('cell_0_8');
        var cell_id = "#cell_0_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_0": function() {

        var cell = document.getElementById('cell_1_0');
        var cell_id = "#cell_1_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_1": function() {

        var cell = document.getElementById('cell_1_1');
        var cell_id = "#cell_1_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_2": function() {

        var cell = document.getElementById('cell_1_2');
        var cell_id = "#cell_1_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_3": function() {

        var cell = document.getElementById('cell_1_3');
        var cell_id = "#cell_1_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_4": function() {

        var cell = document.getElementById('cell_1_4');
        var cell_id = "#cell_1_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_5": function() {

        var cell = document.getElementById('cell_1_5');
        var cell_id = "#cell_1_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_6": function() {

        var cell = document.getElementById('cell_1_6');
        var cell_id = "#cell_1_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_7": function() {

        var cell = document.getElementById('cell_1_7');
        var cell_id = "#cell_1_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_1_8": function() {

        var cell = document.getElementById('cell_1_8');
        var cell_id = "#cell_1_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_0": function() {

        var cell = document.getElementById('cell_2_0');
        var cell_id = "#cell_2_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_1": function() {

        var cell = document.getElementById('cell_2_1');
        var cell_id = "#cell_2_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_2": function() {

        var cell = document.getElementById('cell_2_2');
        var cell_id = "#cell_2_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_3": function() {

        var cell = document.getElementById('cell_2_3');
        var cell_id = "#cell_2_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_4": function() {

        var cell = document.getElementById('cell_2_4');
        var cell_id = "#cell_2_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_5": function() {

        var cell = document.getElementById('cell_2_5');
        var cell_id = "#cell_2_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_6": function() {

        var cell = document.getElementById('cell_2_6');
        var cell_id = "#cell_2_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_7": function() {

        var cell = document.getElementById('cell_2_7');
        var cell_id = "#cell_2_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_2_8": function() {

        var cell = document.getElementById('cell_2_8');
        var cell_id = "#cell_2_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_0": function() {

        var cell = document.getElementById('cell_3_0');
        var cell_id = "#cell_3_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_1": function() {

        var cell = document.getElementById('cell_3_1');
        var cell_id = "#cell_3_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_2": function() {

        var cell = document.getElementById('cell_3_2');
        var cell_id = "#cell_3_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_3": function() {

        var cell = document.getElementById('cell_3_3');
        var cell_id = "#cell_3_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_4": function() {

        var cell = document.getElementById('cell_3_4');
        var cell_id = "#cell_3_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_5": function() {

        var cell = document.getElementById('cell_3_5');
        var cell_id = "#cell_3_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_6": function() {

        var cell = document.getElementById('cell_3_6');
        var cell_id = "#cell_3_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_7": function() {

        var cell = document.getElementById('cell_3_7');
        var cell_id = "#cell_3_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_3_8": function() {

        var cell = document.getElementById('cell_3_8');
        var cell_id = "#cell_3_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_0": function() {

        var cell = document.getElementById('cell_4_0');
        var cell_id = "#cell_4_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_1": function() {

        var cell = document.getElementById('cell_4_1');
        var cell_id = "#cell_4_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_2": function() {

        var cell = document.getElementById('cell_4_2');
        var cell_id = "#cell_4_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_3": function() {

        var cell = document.getElementById('cell_4_3');
        var cell_id = "#cell_4_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_4": function() {

        var cell = document.getElementById('cell_4_4');
        var cell_id = "#cell_4_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_5": function() {

        var cell = document.getElementById('cell_4_5');
        var cell_id = "#cell_4_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_6": function() {

        var cell = document.getElementById('cell_4_6');
        var cell_id = "#cell_4_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_7": function() {

        var cell = document.getElementById('cell_4_7');
        var cell_id = "#cell_4_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_4_8": function() {

        var cell = document.getElementById('cell_4_8');
        var cell_id = "#cell_4_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_0": function() {

        var cell = document.getElementById('cell_5_0');
        var cell_id = "#cell_5_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_1": function() {

        var cell = document.getElementById('cell_5_1');
        var cell_id = "#cell_5_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_2": function() {

        var cell = document.getElementById('cell_5_2');
        var cell_id = "#cell_5_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_3": function() {

        var cell = document.getElementById('cell_5_3');
        var cell_id = "#cell_5_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_4": function() {

        var cell = document.getElementById('cell_5_4');
        var cell_id = "#cell_5_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_5": function() {

        var cell = document.getElementById('cell_5_5');
        var cell_id = "#cell_5_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_6": function() {

        var cell = document.getElementById('cell_5_6');
        var cell_id = "#cell_5_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_7": function() {

        var cell = document.getElementById('cell_5_7');
        var cell_id = "#cell_5_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_5_8": function() {

        var cell = document.getElementById('cell_5_8');
        var cell_id = "#cell_5_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_0": function() {

        var cell = document.getElementById('cell_6_0');
        var cell_id = "#cell_6_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_1": function() {

        var cell = document.getElementById('cell_6_1');
        var cell_id = "#cell_6_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_2": function() {

        var cell = document.getElementById('cell_6_2');
        var cell_id = "#cell_6_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_3": function() {

        var cell = document.getElementById('cell_6_3');
        var cell_id = "#cell_6_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_4": function() {

        var cell = document.getElementById('cell_6_4');
        var cell_id = "#cell_6_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_5": function() {

        var cell = document.getElementById('cell_6_5');
        var cell_id = "#cell_6_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_6": function() {

        var cell = document.getElementById('cell_6_6');
        var cell_id = "#cell_6_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_7": function() {

        var cell = document.getElementById('cell_6_7');
        var cell_id = "#cell_6_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_6_8": function() {

        var cell = document.getElementById('cell_6_8');
        var cell_id = "#cell_6_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_0": function() {

        var cell = document.getElementById('cell_7_0');
        var cell_id = "#cell_7_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_1": function() {

        var cell = document.getElementById('cell_7_1');
        var cell_id = "#cell_7_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_2": function() {

        var cell = document.getElementById('cell_7_2');
        var cell_id = "#cell_7_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_3": function() {

        var cell = document.getElementById('cell_7_3');
        var cell_id = "#cell_7_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_4": function() {

        var cell = document.getElementById('cell_7_4');
        var cell_id = "#cell_7_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_5": function() {

        var cell = document.getElementById('cell_7_5');
        var cell_id = "#cell_7_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_6": function() {

        var cell = document.getElementById('cell_7_6');
        var cell_id = "#cell_7_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_7": function() {

        var cell = document.getElementById('cell_7_7');
        var cell_id = "#cell_7_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_7_8": function() {

        var cell = document.getElementById('cell_7_8');
        var cell_id = "#cell_7_8";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_0": function() {

        var cell = document.getElementById('cell_8_0');
        var cell_id = "#cell_8_0";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_1": function() {

        var cell = document.getElementById('cell_8_1');
        var cell_id = "#cell_8_1";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_2": function() {

        var cell = document.getElementById('cell_8_2');
        var cell_id = "#cell_8_2";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_3": function() {

        var cell = document.getElementById('cell_8_3');
        var cell_id = "#cell_8_3";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_4": function() {

        var cell = document.getElementById('cell_8_4');
        var cell_id = "#cell_8_4";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_5": function() {

        var cell = document.getElementById('cell_8_5');
        var cell_id = "#cell_8_5";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_6": function() {

        var cell = document.getElementById('cell_8_6');
        var cell_id = "#cell_8_6";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_7": function() {

        var cell = document.getElementById('cell_8_7');
        var cell_id = "#cell_8_7";
            this.selectCell(cell, cell_id)
        },
        "click #cell_8_8": function() {

        var cell = document.getElementById('cell_8_8');
        var cell_id = "#cell_8_8";
            this.selectCell(cell, cell_id)
        },

    },

     valid: function (k,l,r1){

        var k1= (Math.floor(k/3))*3;
        var k2=k1+3;
        var l1= (Math.floor(l/3))*3;
        var l2=l1+3;
        for (var i=k1;i<k2;i++)
        {
            for(var j=l1;j<l2;j++)
            {
                if(sudokuboard[i][j]==r1)
                return false;
            }
        }
        for (var m=0;m<9;m++)
        {
            if((sudokuboard[k][m]==r1) | (sudokuboard[m][l]==r1)){
                return false;
            }
        }
        return true;
    },

    keyPress: function(evt)
    {
        var key;
        if (selected_cell_id)
        {
            if (evt)
            {
                key = evt.key;
                var key_no = parseInt(key);
                var rr= selected_cell_id.charAt(6);
                var cc= selected_cell_id.charAt(8);
            }
            if (key == ' ')
            {
                console.log("sudokuboard[rr][cc]", board[rr][cc])
                if(!(board[rr][cc]))
                {
                    console.log("space space", globb, selected_cell_id)
                    $(selected_cell_id).text("");
                    sudokuboard[rr][cc]=0;
                    console.log("sudokuboard[rr][cc]", sudokuboard[rr][cc])
                    if ($(selected_cell_id).hasClass("selected")){
                        console.log("class selected")
                        $(selected_cell_id).addClass('tofill').removeClass('selected');
                    }
                    if ($(selected_cell_id).hasClass("filled")){
                        console.log("class filled")
                        $(selected_cell_id).addClass('tofill').removeClass('filled');
                    }
                }
            }
            else if (key_no >= 1 && key_no <= 9)
            {
                console.log("key + selected_cell_id",key, selected_cell_id);
                var chk = globb.valid(rr,cc,key);
                if (chk==1)
                {
                    $(selected_cell_id).text(key);
                    sudokuboard[rr][cc]=key;
                     $(selected_cell_id).addClass('filled').removeClass('selected');
                    if(globb.isfull(rr, cc))
                    {
                        globb.show_wow()
                        setTimeout(function() {
                            globb.check();
                        }, 10000);
                    }
                }
                else
                    alert("Cannot enter "+key+".Because this number twice in the same row or same column or same box.");
            }
        }
    },

    initialize:function()
    {
        document.onkeypress = this.keyPress;
    },

selectCell: function(cell, cell_id)
    {
    if (checkit)
    {
        for (var rows = 0; rows <=8; rows++)
        {
            for (var cols=0; cols <= 8; cols++)
            {
                var cells=document.getElementById('cell_' + rows + '_' + cols)
                if (cells.className == 'selected')
                {
                    var v= sudokuboard[rows][cols];
                    if (v==0){
                         cells.className = 'tofill';
                    }
                    else{
                        if (sudokuboard[rows][cols] == board[rows][cols])
                        {
                            cells.className = 'notfill';
                        }
                        else
                            cells.className = 'filled';
                    }
                }
            }
        }

        var row = cell_id.charAt(6);
        var col = cell_id.charAt(8);

        if (parseInt(cell.innerHTML))
        {
            if (board[row][col] != 0){
                cell.className='notfill';
            }
            else{
                cell.className='selected';
            }

        }
        else{
            cell.className='selected';
        }
        current_cell = this;
        globb = this;
        selected_cell_id = cell_id
        }
    },

    level: function(lvl)
    {
        for (var i = 1; i <=lvl;)
        {
            var k=this.rand();
            var l=this.rand();
            if (sudokuboard[k][l] == 0)
            {
                var x = Puzzle[k][l];
                var random="cell_"+k+"_"+l;
                    $("#cell_"+k+"_"+l).text(x);
                    sudokuboard[k][l]=x;
                    board[k][l]=x;
                    i++;
            }
        }
        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                var cell = document.getElementById('cell_' + row + '_' + col);
                var self = this;
                var cell_id = "#cell_" + row + "_" + col
                var cell_idd = "cell_" + row + "_" + col
                if (!parseInt(cell.innerHTML))
                {
                    cell.className='tofill';
                }
                else
                {
                    cell.className='notfill';
                }
            }
        }
        this.rese();
    },

    newgame: function()
    {
        $(".sudo").text("SUDOKU");
        this.problem();
        for (var row = 0; row <=8; row++)
        {
            sudokuboard[row]=new Array(9);
            orginalboard[row]=new Array(9);
            board[row]=new Array(9);
            for (var col=0; col <= 8; col++)
            {
                $("#cell_"+row+"_"+col).text("");

                sudokuboard[row][col]=0;
                orginalboard[row][col]=0;
                board[row][col]=0;
            }
        }
    },

    validd:function (randVal,thisRow,thisCol,subMat)
    {
        for(var i=0;i<9;i++)
        {
            if(thisRow[i]==randVal)
            {
                return 1;
            }
            else if (thisCol[i]==randVal)
            {
                return 1;
            }
            else if(subMat[i]==randVal)
            {
                return 1;
            }
            else
            {
                continue;
            }
        }
        return 0;
    },

    rand: function()
    {
        var r1=Math.floor(Math.random() * 10);
        r1=(r1+r1+1)%9
            return r1;
    },

    checkback: function()
    {
        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                var cell=document.getElementById('cell_' + row + '_' + col)
                var cell_id = '#cell_' + row + '_' + col
                var v= sudokuboard[row][col];
                if (v==0){
                     $("#cell_"+row+"_"+col).text("");
                     cell.className = 'tofill';
                }
                else{
                    $("#cell_"+row+"_"+col).text(v);
                    console.log("receckkkkk",sudokuboard[row][col] )
                    if (sudokuboard[row][col] == board[row][col])
                    {
                        cell.className = 'notfill';
                    }
                    else
                        cell.className = 'filled';

                }

           }
        }
    },

    show_wow: function() {
        var class_to_add = 'o_wow_thumbs';
        var $body = $('body');
        $body.addClass(class_to_add);
        setTimeout(function() {
            $body.removeClass(class_to_add);
        }, 10000);
    },

    show_lost: function() {
        var class_to_add = 'o_lost_thumbs';
        var $body = $('body');
        $body.addClass(class_to_add);
        setTimeout(function() {
            $body.removeClass(class_to_add);
        }, 10000);
    },

    check: function()
    {
        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                var cell = document.getElementById('cell_' + row + '_' + col);
                if (Puzzle[row][col]==sudokuboard[row][col])
                    cell.className='green';
                else
                    cell.className='red';
            }
        }
    },

    solve: function()
    {

        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                var val=Puzzle[row][col];
                $("#cell_"+row+"_"+col).text(val);
                sudokuboard[row][col]=val;
            }
        }

    },

    rese: function()
    {
        this.initialize();
        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                sudokuboard[row][col]=board[row][col];
                var cell=document.getElementById('cell_' + row + '_' + col)
                var cell_id = '#cell_' + row + '_' + col
                var cell_idd = 'cell_' + row + '_' + col
                var v= board[row][col];
                if (v==0)
                     $("#cell_"+row+"_"+col).text("");
                else{
                    $("#cell_"+row+"_"+col).text(v);
                }
                if (!parseInt(cell.innerHTML))
                {
                    cell.className = 'tofill';
                }
                else
                    cell.className = 'notfill';
            }

        }
    },

    isfull:function (rr, cc)
    {
        for (var row = 0; row <=8; row++)
        {
            for (var col=0; col <= 8; col++)
            {
                if (!(row == rr && col == cc)){
                    var cell = document.getElementById('cell_' + row + '_' + col);
                        console.log("isfullllllllllllllllllll",cell, cell.innerHTML);
                        if (!parseInt(cell.innerHTML))
                        {
                            return false;
                        }
                }
            }
        }
        return true;
    },

    problem: function(){

  			var count=101;
  			while(count>maxAttempts)
  			{
   				for(var m=0;m<9;m++)
   				{
       				Puzzle[m]=new Array(9);
    				for(var n=0;n<9;n++)
    				{
     					Puzzle[m][n]=0;
    				}
   				}
	   			for(var row=0;row<9;row++)
	   			{
		   			for(var col=0;col<9;col++)
		   			{
		   				thisRow=Puzzle[row];
		   				thisCol=new Array();
		   				for(var row1=0;row1<9;row1++)
		   				{
		   					thisCol.push(Puzzle[row1][col]);
		   				}
		   				var subRow=parseInt(row/3);
		   				var subCol=parseInt(col/3);
		   				var subMat=new Array();
		   				for(var subR=0;subR<3;subR++)
		   				{
		   					for(var subC=0;subC<3;subC++)
		   					{
		   						subMat.push(Puzzle[(subRow*3)+subR][(subCol*3)+subC]);
		   					}
		   				}
		   				var randVal=0;
		   				count=0;
		   				while(this.validd(randVal,thisRow,thisCol,subMat))
		   				{
		   					randVal=this.rand();
		   					if (randVal==0)
		   						randVal=9;
		   					count+=1;
		   					if(count>maxAttempts)
		   					{
		   						break;
		   					}
		   				}
		   				Puzzle[row][col]=randVal;
		   				if(count>maxAttempts)
		   				{
		   					break;
		   				}


	   				}
		   			if(count>maxAttempts)
		   			{
		   				break;
		   			}
		   		}

	   		}
   		},

start: function () {
        var self = this;
        var hr_employee = new Model('hr.employee');
        hr_employee.query(['attendance_state', 'name'])
            .filter([['user_id', '=', self.session.uid]])
            .all()
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.user = self.session.uid
                self.$el.html(QWeb.render("EntertainmentGamesSudoku", {widget: self}));
            });

        return this._super.apply(this, arguments);
    },
});
core.action_registry.add('entertainment_games_sudoku', Sudoku);

return Sudoku;

});
