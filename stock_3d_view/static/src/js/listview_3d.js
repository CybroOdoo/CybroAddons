odoo.define('button_near_create.tree_button', function(require) {
	"use strict";
	var ListController = require('web.ListController');
	var ListView = require('web.ListView');
	var viewRegistry = require('web.view_registry');
	var core = require('web.core');
	var session = require('web.session');
	var Dialog = require('web.Dialog');
	var QWeb = core.qweb;
	var rpc = require('web.rpc');
	var ajax = require('web.ajax');
	var PositionDialog = Dialog.extend({
		/**
		 * Initialize the PositionDialog.
		 *
		 * @param {Object} parent - The parent object.
		 * @param {Object} options - Dialog options.
		 * @param {Object} pointer - Object containing x and y coordinates.
		 * @param {Function} close - Function to be called on dialog close.
		 */
		init: function(parent, options) {
			var opt = options;
			this._super(...arguments)
			this.pointer = opt.pointer
			this.onClickClose = opt.close
		},
		/**
		 * Render the PositionDialog element.
		 * Set the dialog's position based on the provided coordinates.
		 */
		renderElement: function() {
			this._super()
			this.$modal.find('.modal-dialog').css({
				position: 'absolute',
				left: this.pointer.x,
				top: this.pointer.y,
			})
		}
	})
	//Extends list controller class to add event listener for 3D button.
	var TreeButton = ListController.extend({
		buttons_template: 'StockLocationListView',
		events: _.extend({}, ListController.prototype.events, {
			'click .open_3d_view': '_Open3DView',
		}),
		/**
		 * Starts the process of displaying rendered 3D object of stock.location.
		 */
		_Open3DView: async function(ev) {
			var self = this;
			var wh_data;
			var data;
			var loc_quant;
			let controls, renderer, clock, scene, camera, pointer, raycaster;
			var mesh, group;
			var material;
			var loc_color;
			var loc_opacity = 0.5;
			var textSize;
			let selectedObject = null;
			var dialogs = null;
			var wh_id;
			/**
			 * Make a jsonRpc call to fetch available warehouses and list it in the dropdown.
			 *
			 * @await
			 * @param {integer} company_id
			 */
			await ajax.jsonRpc('/3Dstock/warehouse', 'call', {
				'company_id': session.user_context.allowed_company_ids[0],
			}).then(function(incoming_data) {
				wh_data = incoming_data;
			});
			wh_id = wh_data[0][0];
			var select = document.createElement("select");
			select.name = "mySelect";
			for (let i = 0; i < wh_data.length; i++) {
				var option = document.createElement("option");
				option.value = wh_data[i][0];
				option.text = wh_data[i][1];
				select.appendChild(option);
				select.classList.add("customselect");
			}

			var closeDiv = document.createElement("button");
			closeDiv.classList.add("closeBtn");
			closeDiv.innerHTML = "&times;"
			var colorDiv = document.createElement("div");
			colorDiv.classList.add("rectangle");
			var color1 = document.createElement("div");
			color1.classList.add("square1");
			colorDiv.appendChild(color1);
			var colorText1 = document.createElement("div");
			colorText1.classList.add("squareText1");
			colorText1.innerHTML = "Overload";
			colorDiv.appendChild(colorText1);
			var color2 = document.createElement("div");
			color2.classList.add("square2");
			colorDiv.appendChild(color2);
			var colorText2 = document.createElement("div");
			colorText2.classList.add("squareText2");
			colorText2.innerHTML = "Almost Full";
			colorDiv.appendChild(colorText2);
			var color3 = document.createElement("div");
			color3.classList.add("square3");
			colorDiv.appendChild(color3);
			var colorText3 = document.createElement("div");
			colorText3.classList.add("squareText3");
			colorText3.innerHTML = "Free Space Available";
			colorDiv.appendChild(colorText3);
			var color4 = document.createElement("div");
			color4.classList.add("square4");
			colorDiv.appendChild(color4);
			var colorText4 = document.createElement("div");
			colorText4.classList.add("squareText4");
			colorText4.innerHTML = "No Product/Load";
			colorDiv.appendChild(colorText4);

			start();
			/**
			 * The complete working of fetching data from stock.location and displaying them in the form of 3d objects.
			 *
			 * @async
			 */
			async function start() {
				/**
				 * Make a jsonRpc call to fetch location details of corresponding warehouse.
				 *
				 * @await
				 * @param {integer} company_id
				 * @param {integer} wh_id
				 */
				await ajax.jsonRpc('/3Dstock/data', 'call', {
					'company_id': session.user_context.allowed_company_ids[0],
					'wh_id': wh_id,
				}).then(function(incoming_data) {
					data = incoming_data;
				});
				scene = new THREE.Scene();
				scene.background = new THREE.Color(0xdfdfdf);
				clock = new THREE.Clock();
				camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.5, 6000);
				camera.position.set(0, 200, 300)
				renderer = new THREE.WebGLRenderer({
					antialias: true
				});
				renderer.setSize(window.innerWidth, window.innerHeight / 1.164);
				renderer.setPixelRatio(window.devicePixelRatio);
				renderer.render(scene, camera);
				self.$el.find('.o_content').html(renderer.domElement);
				self.$el.find('.o_content').append(select);
				self.$el.find('.o_content').append(colorDiv);
				self.$el.find('.o_content').append(closeDiv);
				var dropdown = document.querySelector(".customselect");
				if (dropdown) {
					dropdown.addEventListener("change", warehouseChange);
				}
				var closeBtn = document.querySelector(".closeBtn");
				if (closeBtn) {
					closeBtn.addEventListener("click", onWindowClose);
				}
				controls = new THREE.OrbitControls(camera, renderer.domElement);
				const baseGeometry = new THREE.BoxGeometry(800, 0, 800);
				const baseMaterial = new THREE.MeshBasicMaterial({
					color: 0xffffff,
					transparent: false,
					opacity: 1,
					side: THREE.BackSide,
				});
				const baseCube = new THREE.Mesh(baseGeometry, baseMaterial);
				scene.add(baseCube);
				group = new THREE.Group();
				//traversing through each location object
				for (let [key, value] of Object.entries(data)) {
					//checks if the dimension values of the location are non zero
					if ((value[0] > 0) || (value[1] > 0) || (value[2] > 0) || (value[3] > 0) || (value[4] > 0) || (value[5] > 0)) {
						const geometry = new THREE.BoxGeometry(value[3], value[5], value[4]);
						geometry.translate(0, (value[5] / 2), 0);
						const edges = new THREE.EdgesGeometry(geometry);
						/**
						 * Make a jsonRpc call to fetch the stock details of particular location.
						 *
						 * @await
						 * @param {integer} loc_code
						 */
						await ajax.jsonRpc('/3Dstock/data/quantity', 'call', {
							'loc_code': key,
						}).then(function(quant_data) {
							loc_quant = quant_data;
						});
						//checking the quantity and capacity of the location to determine the color of the location
						if (loc_quant[0] > 0) {
							if (loc_quant[1] > 100) {
								loc_color = 0xcc0000;
								loc_opacity = 0.8;
							} else if (loc_quant[1] > 50) {
								loc_color = 0xe6b800;
								loc_opacity = 0.8;
							} else {
								loc_color = 0x00802b;
								loc_opacity = 0.8;
							}
						} else {
							if (loc_quant[1] == -1) {
								loc_color = 0x00802b;
								loc_opacity = 0.8;
							} else {
								loc_color = 0x8c8c8c;
								loc_opacity = 0.5;
							}
						}
						//creating a 3D box geometry for each location
						material = new THREE.MeshBasicMaterial({
							color: loc_color,
							transparent: true,
							opacity: loc_opacity
						});
						mesh = new THREE.Mesh(geometry, material);
						const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
							color: 0x404040
						}));
						line.position.x = value[0];
						line.position.y = value[1];
						line.position.z = value[2];
						mesh.position.x = value[0];
						mesh.position.y = value[1];
						mesh.position.z = value[2];
						const loader = new THREE.FontLoader();
						loader.load('https://threejs.org/examples/fonts/droid/droid_sans_bold.typeface.json', function(font) {
							const textcolor = 0x000000;
							const textMat = new THREE.MeshBasicMaterial({
								color: textcolor,
								side: THREE.DoubleSide,
							});
							const textmessage = key;
							if (value[3] > value[4]) {
								textSize = (value[4] / 2) - (value[4] / 2.9);
							} else {
								textSize = (value[3] / 2) - (value[3] / 2.9);
							}
							const textshapes = font.generateShapes(textmessage, textSize);
							const textgeometry = new THREE.ShapeGeometry(textshapes);
							textgeometry.translate(0, ((value[5] / 2) - (textSize / (textSize - 1.5))), 0);
							const text = new THREE.Mesh(textgeometry, textMat);
							if (value[4] > value[3]) {
								text.rotation.y = Math.PI / 2;
								text.position.x = value[0];
								text.position.y = value[1];
								text.position.z = value[2] + (textSize * 2) + ((value[3] / 3.779 / 2) / 2) + (textSize / 2);
							} else {
								text.position.x = value[0] - (textSize * 2) - ((value[4] / 3.779 / 2) / 2) - (textSize / 2);
								text.position.y = value[1];
								text.position.z = value[2];
							}
							scene.add(text);
						});
						scene.add(mesh);
						scene.add(line);
						mesh.name = key;
						mesh.userData = {
							color: loc_color
						};
						group.add(mesh);
					}
				}
				scene.add(group);
				raycaster = new THREE.Raycaster();
				pointer = new THREE.Vector3();

				animate();
			}
			/**
			 * Triggered when users change warehouse and calls the start() function with the latest warehouse id.
			 */
			function warehouseChange() {
				console.log('111111111111111111111111111111111')
				var selectedBox = document.querySelector(".customselect");
				var selectValue = selectedBox.value;
				wh_id = selectValue;
				start();
			}
			/**
			 * Handles the resizing and setting the pixel ration on window resize.
			 */
			function onWindowResize() {
				camera.aspect = window.innerWidth / window.innerHeight;
				camera.updateProjectionMatrix();
				renderer.setSize(window.innerWidth, window.innerHeight / 1.164);
			}
			/**
			 * Triggered when user clicks on close button.
			 */
			function onWindowClose() {
				window.location.reload();
			}
			/**
			 * Animates and renders the three.renderer object to make changes on the scene.
			 */
			function animate() {
				requestAnimationFrame(animate);
				const delta = clock.getDelta();
				renderer.render(scene, camera);
				var canvas = document.getElementsByTagName("canvas")[0];
				var selectedBox = document.querySelector(".customselect");
				var colorBox = document.querySelector(".rectangle");
				var closeDiv = document.querySelector(".closeBtn");
				//checking the canvas element adding event listener on canvas.
				if (canvas == null) {
					window.removeEventListener('dblclick', onPointerMove);
					window.removeEventListener('resize', onWindowResize);
					if (selectedBox) {
						selectedBox.style.display = "none";
					}
					if (colorBox) {
						colorBox.style.display = "none";
					}
					if (closeDiv) {
						closeDiv.style.display = "none";
					}
				} else {
					window.addEventListener('dblclick', onPointerMove);
					window.addEventListener('resize', onWindowResize);
					if (selectedBox) {
						selectedBox.style.display = "block";
					}
					if (colorBox) {
						colorBox.style.display = "block";
					}
					if (closeDiv) {
						closeDiv.style.display = "block";
					}
				}
			}
			/**
			 * gets the coordinates of the mouse point and checks for any objects.
			 *
			 * @async
			 * @param {object} event
			 */
			async function onPointerMove(event) {
				var products;
				var button;
				if (dialogs == null) {
					if (selectedObject) {
						selectedObject.material.color.set(selectedObject.userData.color);
						selectedObject = null;
					} else {
						pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
						pointer.y = -(event.clientY / (window.innerHeight)) * 2 + 1 + 0.13;
						raycaster.setFromCamera(pointer, camera);
						const intersects = raycaster.intersectObject(group, true);
						if (intersects.length > 0) {
							const res = intersects.filter(function(res) {
								return res && res.object;
							})[0];
							if (res && res.object) {
								/**
								 * Make a jsonRpc call to fetch the details of products and their quantity of selected location.
								 *
								 * @await
								 * @param {integer} loc_code
								 */
								await ajax.jsonRpc('/3Dstock/data/product', 'call', {
									'loc_code': res.object.name,
								}).then(function(product_data) {
									products = product_data;
								});
								selectedObject = res.object;
								selectedObject.material.color.set(0x00ffcc);

								function onClickClose() {
									if (selectedObject) {
										selectedObject.material.color.set(selectedObject.userData.color);
										selectedObject = null;
										dialogs.close();
										dialogs = null;
									}
								}
								//opens a new dialogbox with proeduct and quantity details
								dialogs = new PositionDialog(this, {
									title: ('Location: ' + res.object.name),
									size: 'small',
									$content: $(QWeb.render('ViewLocationData', {
										data: products,
									})),
									placement: 'bottom',
									renderFooter: false,
									pointer: {
										x: event.clientX,
										y: event.clientY,
									},
									close: onClickClose,
								}).open();

								if (dialogs) {
									window.addEventListener('click', onClickClose);
								} else {
									window.removeEventListener('click', onClickClose);
								}
							}
						}
					}
				}
			}
		}
	});
	var StockLocationTreeView = ListView.extend({
		config: _.extend({}, ListView.prototype.config, {
			Controller: TreeButton,
		}),
	});
	viewRegistry.add('3d_button_in_stock', StockLocationTreeView);
});