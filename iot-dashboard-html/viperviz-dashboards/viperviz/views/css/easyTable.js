/*
 Table plugin for jQuery
 Copyright (c) 2016 Gabriel Rodrigues e Gabriel Leite (http://gabrielr47.github.io/)
 Licensed under the MIT license
 Version: 0.2
 */
 /*Modiffied by OTICS advanced analytics Inc.
 Copyright 2020
 */

$.fn.easyTable = function (options) {
   var trIndex = 'all';
   this.options = {
      tableStyle: 'table easyTable',
      hover: 'btn-success',
      buttons: true,
      select: true,
      sortable: true,
      scroll: {active: false, height: '400px'}
   };
   this.message = {
      all: 'Select All',
      clear: 'Clear',
      search: 'Search'
   };
   this.select = function () {
      var table = this;
      var options = this.options;
      var posCurrentTr = 0;
      var pressCrl = false;
      var pressShift = false;
      var pressDir = '';
      var posIniShift = 0;
      var maxLength = table.find('tbody tr').length - 1;
	 // maxLength=1200;
      table.find('tbody').on('click', 'tr', function () {
		
         if (pressCrl) {
            $(this).toggleClass(options.hover);
            posCurrentTr = $(this).index();
            posIniShift = posCurrentTr;
         } else if (pressShift) {
            $(this).toggleClass(options.hover);
         } else {
            table.find('tbody tr').removeClass(options.hover);
            $(this).addClass(options.hover);
            posCurrentTr = $(this).index();
            posIniShift = posCurrentTr;
         }
      });

      table.on('keydown', function (e) {
  //       posCurrentTr++;
         if ((e.which === 40)) {
            if (posCurrentTr < (maxLength)) {
               if (pressDir === '') {
                  pressDir = 'Down';
			//	   table.find('tbody tr').eq(posCurrentTr).click();
 //posCurrentTr++;
               }
			     
               if (pressDir === 'Up' && (posCurrentTr < posIniShift)) {
                  table.find('tbody tr').eq(posCurrentTr).click();
                 posCurrentTr++;
				   table.find('tbody tr').eq(posCurrentTr).click();
				    
               } else if ((posCurrentTr === posIniShift) && (pressDir !== 'Down')) {
                  pressDir = '';
                   posCurrentTr++;
                  table.find('tbody tr').eq(posCurrentTr).click();
				 
               } else {
                  posCurrentTr++;
                  if (!table.find('tbody tr').eq(posCurrentTr).hasClass(options.hover)) {
                     table.find('tbody tr').eq(posCurrentTr).click();
					 
                  }
				  
               }
            }
			
         } else if ( (e.which === 38)) {
            if (posCurrentTr > 0) {
               if (pressDir === '') {
                  pressDir = 'Up';
               }
               if (pressDir === 'Down' && (posCurrentTr > posIniShift)) {
                  table.find('tbody tr').eq(posCurrentTr).click();
                  posCurrentTr--;
               } else if ((posCurrentTr === posIniShift) && (pressDir !== 'Up')) {
                  pressDir = '';
                  posCurrentTr--;
                  table.find('tbody tr').eq(posCurrentTr).click();
               } else {
                  posCurrentTr--;
                  if (!table.find('tbody tr').eq(posCurrentTr).hasClass(options.hover)) {
                     table.find('tbody tr').eq(posCurrentTr).click();
                  }
               }
            }

         } else if (e.which === 16) {
            pressShift = true;
         } else if (e.which === 17) {
            pressCrl = true;
         }

      });

      table.on('keyup', function (e) {
         if (e.which === 16) {
            pressShift = false;
         } else if (e.which === 17) {
            pressCrl = false;
         }
      });
   };
   this.sortable = function () {
      function sortTr(table, col, reverse) {
		  if (col==0){
			  return;
		  }
         var tb = table.tBodies[0];
         var tr = Array.prototype.slice.call(tb.rows, 0);
         var i;
         reverse = -((+reverse) || -1);
         var str1;
         var str2;
         tr = tr.sort(function (a, b) {

            if (a.cells[col].children[0] === undefined) {
               str1 = a.cells[col].textContent.trim();
               str2 = b.cells[col].textContent.trim();
            } else {
               str1 = a.cells[col].getElementsByTagName(a.cells[col].children[0].tagName)[0].value;
               str2 = b.cells[col].getElementsByTagName(a.cells[col].children[0].tagName)[0].value;
            }

            if (!isNaN(str1)) {
               if (str1.length === 1) {
                  str1 = '0' + str1;
               }
               if (str2.length === 1) {
                  str2 = '0' + str2;
               }
            }
            return reverse * (str1.localeCompare(str2, 'en', {numeric: true}));
         });

         for (i = 0; i < tr.length; ++i) {
            tb.appendChild(tr[i]);
         }
      }

      this.makeSortable = function (table) {
         var th = table.tHead;
         var tablePlugin = this;
         var i;
         th && (th = th.rows[0]) && (th = th.cells);

         if (th) {
            i = th.length;
         } else {
            return;
         }

         while (--i > 0) {
            (function (i) {
               var dir = 1;
               $(th[i]).append(' <i class="fa fa-sort-amount-asc  hidden" data-order="up"></i>');
               $(th[i]).append(' <i class="fa fa-sort-amount-desc hidden" data-order="down"></i>');
               $(th[i]).click(function () {
                  trIndex = $(th[i]).index();
                  $("#search").attr('placeholder', tablePlugin.message.search + ' ' + $(th[i]).text());
                  sortTr(table, i, (dir = 1 - dir));
                  if ((1 - dir) === 1) {
                     $(th).find('i[data-order=down],i[data-order=up]').addClass('hidden');
                     $(th[i]).find('i[data-order=up]').removeClass('hidden');
										
                  } else {
                     $(th).find('i[data-order=down],i[data-order=up]').addClass('hidden');
                     $(th[i]).find('i[data-order=down]').removeClass('hidden');
					 
                  }
               });
            }(i));
         }
      };

      this.makeAllSortable = function (table) {
         var t = table;
         var i = t.length;
         while (--i >= 0) {
            this.makeSortable(t[i]);
         }
      };

      this.makeAllSortable(this);

   };
   this.buttons = function (tbl) {
      var table = this;
      
     var all = '';
	 var clear='';
	//  var all = '<button id=\'all\' class=\'btn ' + this.options.hover + ' btn-sm\' ' +
      //        'data-toggle=\'tooltip\' data-placement=\'top\' title=\'' + this.message.all + '\'><i class=\'fa fa-check\'></i></button>';
    //  var clear = '<button  id=\'clear\' class=\'btn btn-danger btn-sm\'  ' +
      //        'data-toggle=\'tooltip\' data-placement=\'top\' title=\'' + this.message.clear + '\'><i class=\'fa fa-close\'></i></button> <a href=\'../../maadsweb/grids/griddata.csv\' //target=blank>Grid Data</a>';
	var menu = '<div id=\'easyMenuTable'+tbl+'\' class=\'row\'>' + clear + '<div class=\'col-md-3 pull-left\'></div> <div class=\'col-md-6 pull-right\'></div></div>';
	
      this.parent().prepend(menu);
      var menuId = $("#easyMenuTable"+tbl+" .pull-left");
      menuId.append(all);
      $('[data-toggle="tooltip"]').tooltip();
      all = $("#easyMenuTable"+tbl+" .pull-left #all");
      clear = $("#easyMenuTable"+tbl+" .pull-left #clear");
      if (this.options.select) {
         all.click(function () {
            table.find('tbody tr').addClass(table.options.hover);
			return false;
         });
         clear.click(function () {
            table.find('tbody tr').removeClass(table.options.hover);
         });
      } //else {
         //console.log('allow the method select to this work');
      //}
   };
   this.filter = function (tbl,label) {
      var table = this;
	  var ms="#easyMenuTable"+tbl;
      var menuId = $(ms +" .pull-left");
      var search = '<input type=\'text\' size=\'50\' class=\'form-control\' placeholder=\'' + this.message.search + '\' id=\'search'+tbl+'\'>';
	 // var Lista = "";
	  //alert(search);
	  
	    
      menuId.prepend(search);
      if (trIndex === 'all') {
         $("#search"+tbl).attr('placeholder', $("#search"+tbl).attr('placeholder') + ' ' + label);
		 
      } 
      $("#search"+tbl).keyup(function () {
         var colunaSel = false;
       //  var termo = $(this).val().toLowerCase();
		 var termo=$("#search"+tbl).val().toLowerCase();
		 sessionStorage.setItem("search"+tbl, termo);
		 //alert(termo);
		 
         table.find('tbody tr').each(function () {
			  //colunaSel = false;
            //if (trIndex === 'all') {
               var td = $(this).find('td');
          //  }// else {
               //var td = $(this).find("td:eq(" + trIndex + ")");
            //}
			
		//	alert(trIndex);
		//	var texts = $("td").map(function() {
			//	return $(this).text();
			//});
			//texts .toString();
			//console.log(texts);
			
           if (td.text().toLowerCase().indexOf(termo) > -1) {
			 // if (texts.toString().toLowerCase().indexOf(termo) > -1) {  
               colunaSel = true;
			   //alert("FOUND");
            }
			
			
            if ((!colunaSel)) {
               $(this).hide();
			 //  alert("hide");
            } else{
				//alert("show");
               $(this).show();
			}
            colunaSel = false;

         });
      });
   };
 this.filtercheckbox = function (tbl) {
      var table = this;
	       
         table.find('tbody tr').each(function () {
             if($(this).is(":visible")){
				// alert("visible")
				  var $cb = $(this).find('input:checkbox'),
				tv=$cb.attr('checked');
				
				if ($cb.prop('checked')) {
				//alert('Checked');
				$cb.prop('checked', false);
				}
				else{
				//	alert('unchecked');
					$cb.prop('checked', true);
				}
				
				//alert("visible"); 
			 }          
			
         });
     // });
   };
    
  
   this.filter2 = function () {
      var table = this;
      var menuId = $("#easyMenuTable .pull-left");
      var search = '<input type=\'text\' class=\'form-control\' placeholder=\'' + this.message.search + '\' id=\'searchproducer\'>';
      menuId.prepend(search);
      if (trIndex === 'all') {
         $("#searchproducer").attr('placeholder', $("#searchproducer").attr('placeholder') + ' Consumers');
      } else {
      }
      $("#searchproducer").keyup(function () {
         var colunaSel = false;
         var termo = $(this).val().toLowerCase();
         table.find('tbody tr').each(function () {
            if (trIndex === 'all') {
               var td = $(this).find('td');
            } else {
               var td = $(this).find("td:eq(" + trIndex + ")");
            }
            if (td.text().toLowerCase().indexOf(termo) > -1) {
               colunaSel = true;
            }
            if ((!colunaSel)) {
               $(this).hide();
            } else
               $(this).show();
            colunaSel = false;

         });
      });
   };
   this.scroll = function () {
      this.find('tbody').css('height', this.options.scroll.height);
   };
   this.getSelected = function (col) {
      var selected = [];
      this.find('tbody .' + this.options.hover).each(function (key, val) {
         selected.push($(val).find('td').eq(col).text());
      });
	  
		    
      return selected;
   };
   this.getSelectedcheckbox = function () {
      var selected = [];
       var table = this;
	       
         table.find('tbody tr').each(function () {
             if($(this).is(":visible")){
				// alert("visible")
				  var $cb = $(this).find('input:checkbox'),
				tv=$cb.attr('checked');
				
				if ($cb.prop('checked')) {
				//alert('Checked');
				 selected.push($cb.prop('id'));
				}
				
				
				//alert("visible"); 
			 }          
			
         });
	//	    alert(selected);
      return selected;
   };
   this.getSearchbox = function (typeid) {
      var selected = "";
	  //alert("#"+typeid);
         selected=$("#"+typeid).val();
     	    
      return selected;
   };
   this.setSearchbox = function (typeid,tvalue) {
     // var selected = "";
	  //alert("#"+typeid);
         $("#"+typeid).val(tvalue);
		 var e = jQuery.Event("keydown");
		e.which = 50; // # Some key code value
		$("#"+typeid).trigger(e);
		$("#"+typeid).trigger('keyup');

     // return selected;
   };
   this.create = function () {
      $("#easyMenuTable" +this.options.buttons.type).remove();
      this.options = $.extend({}, this.options, options);
      this.addClass(this.options.tableStyle);
      this.attr('tabindex', 0);

      if (this.options.select) {
         this.select();
		
      }
      if (this.options.sortable) {
         this.sortable();
      }
      if (this.options.buttons.active) {
         this.buttons(this.options.buttons.type);
         this.filter(this.options.buttons.type,this.options.buttons.label);
		 //this.filter2();
      }
      if (this.options.scroll.active) {
         this.scroll();
      }
   };
   this.create();
   return this;
};

