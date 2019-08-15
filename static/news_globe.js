// Cesium init

Cesium.Ion.defaultAccessToken = '';
default_view_models = Cesium.createDefaultImageryProviderViewModels();
selectedImagery = default_view_models[0];
var viewer = new Cesium.Viewer('cesiumContainer', {
        //baseLayerPicker:false,
        imageryProviderViewModels : default_view_models,
        selectedImageryProviderViewModel : selectedImagery,
        contextOptions : {
            alpha : true
        },
        vrButton : false,
        geocoder : true,
        infoBox : false,
        timeline : false,
        navigationHelpButton : true,
        navigationInstructionsInitiallyVisible : false,
        shadows : false,
        sceneModePicker : true,
        animation : false,
        homeButton : false,
        skyAtmosphere : false
    });

viewer.scene.skyBox.destroy();
viewer.scene.skyBox = undefined;
viewer.scene.sun.destroy();
viewer.scene.sun = undefined;
viewer.scene.moon.destroy();
viewer.scene.moon = undefined;
viewer.scene.fog.enabled = false;

viewer.scene.globe.atmosphereHueShift = -1.0;
viewer.scene.globe.atmosphereSaturationShift = 0.0;
viewer.scene.globe.atmosphereBrightnessShift = 0.0;
viewer.scene.globe.showGroundAtmosphere = false;


viewer.scene.backgroundColor = new Cesium.Color(0, 0, 0, 0);

//Layout

var rainbow = new Rainbow();
rainbow.setSpectrum("#FFC0CB", "#990000");

var info_box = document.getElementsByClassName("cesium-navigation-help cesium-navigation-help")[0];
info_box.innerHTML = '<div class="cesium-click-navigation-help cesium-navigation-help-instructions cesium-click-navigation-help-visible" data-bind="css:{&quot;cesium-click-navigation-help-visible&quot; : !_touch}"> <table> <style>div{font-size: 12px; font-family: Arial;}</style> <tbody> <tr> <td> <div style="color:white ; font-weight: bold;font-size:">Mouse movement</div></td></tr><tr> <td> <div style="color:#40a0e0;">Pan view</div></td><td>Left click + drag</td></tr><tr> <td> <div style="color:#98FB98;">Zoom view</div></td><td> <div>Right click + drag, or</div><div>Mouse wheel scroll</div></td></tr><tr height="10px"></tr><tr> <td> <div style="color:white; font-weight: bold;">Touch movement</div></td></tr><tr> <td> <div style="color:#40a0e0;">Pan view</div></td><td> <div>One finger drag</div></td></tr><tr> <td> <div style="color:#98FB98;">Zoom view</div></td><td> <div>Two finger pinch</div></td></tr><tr height="10px"></tr><tr> <td> <div style="color:white; font-weight: bold;">Usage</div></td></tr><tr> <td> <div>View news</div></td><td> <div>Click on the <span style="color:red">circles</span> </div></td></tr><tr> <td> <div>Read news</div></td><td> <div>Click on titles to be redirected to original news site</div></td></tr><tr> <td> <div>Change time</div></td><td> <div>To adjust time range, use <span style="color:turquoise">slider</span> below (up to 1 week ago)</div></td></tr><tr> <td> <div>Movement</div></td><td> <div>To move camera across globe, use arrow keys.</div></td></tr><tr> <td> <div>Jumping</div></td><td> <div>To jump to adjacent news, use CTRL + arrow keys</div></td></tr></tbody> </table></div>';
var help_button_wrapper = document.getElementsByClassName("cesium-navigationHelpButton-wrapper")[0];
help_button_wrapper.style.zIndex = "1";
var help_button = help_button_wrapper.childNodes[0]; 
var base_picker = document.getElementsByClassName("cesium-baseLayerPicker-dropDown")[0];
base_picker.style.zIndex = "1";

document.getElementsByClassName("cesium-viewer-bottom")[0].style.opacity = 0;

var fullscreen_button = document.getElementsByClassName("cesium-viewer-fullscreenContainer")[0];
fullscreen_button.style.top = "7px";
fullscreen_button.style.right = "8px";
fullscreen_button.style.width = "32px";
fullscreen_button.style.height = "32px";

var viewer_toolbar = document.getElementsByClassName("cesium-viewer-toolbar")[0];
viewer_toolbar.style.right = "44px";

var elems = Array.prototype.slice.call(document.querySelectorAll('.js-switch'));
elems.forEach(function (html) {
    "use strict";
    new Switchery(html, {
        size : "small"
    });
});

function date_midnight(date, daysmodifier) {
    "use strict";
    if (date === null) {
        date = new Date();
    }
    var str_date_from = date_to_str(date);
    var date_out = new Date(str_date_from);
    date_out.setDate(date_out.getDate() + daysmodifier);
    return date_out;
}

var dateSlider = document.getElementById('slider');

var format = wNumb({
        encoder : function (a) {
            "use strict";
            return a;
        },
        edit : function (a) {
            "use strict";
            a = parseInt(a);
            var da = new Date(a);
            var y_m_d = da.toISOString().split("T")[0];
            var y_m_d_array = y_m_d.split('-');
            var str = y_m_d_array[2].replace(/^0+/, '') + '.' + y_m_d_array[1].replace(/^0+/, '') + '.';
            return str;
        }
    });

noUiSlider.create(dateSlider, {
    // Create two timestamps to define a range.
    range : {
        min : date_midnight(null, -7).getTime(),
        max : date_midnight(null, 1).getTime()
    },
    tooltips : [format, format],

    // Steps of one week
    step : 24 * 60 * 60 * 1000,

    // Two more timestamps indicate the handle starting positions.
    start : [date_midnight(null, -0).getTime(), date_midnight(null, 1).getTime()],

    // No decimals
    format : wNumb({
        decimals : 0
    }),

    connect : true,

    behaviour : 'tap-drag'

});

dateSlider.noUiSlider.on('update', function (values) {
    "use strict";
    var dateFrom = new Date(parseInt(values[0]));
    var dateTo = new Date(parseInt(values[1]));
    window.timeFrom = dateFrom.getTime();
    window.timeTo = dateTo.getTime();
});

dateSlider.noUiSlider.on('set', function () {
    "use strict";
    if (counted_articles != null) {
        news_container.hideContainer();
        refresh();
    }
});

dateSlider.noUiSlider.on('start', function () {
    "use strict";
    var tooltips = document.getElementsByClassName("noUi-tooltip");
    var i = 0;
    for (i; i < tooltips.length; i += 1) {
        var t = tooltips[i];
        t.style.opacity = 1;
    }
});

dateSlider.noUiSlider.on('end', function () {
    "use strict";
    var tooltips = document.getElementsByClassName("noUi-tooltip");
    var i = 0;
    for (i; i < tooltips.length; i += 1) {
        var t = tooltips[i];
        t.style.opacity = 0;
    }
    save_to_cache("slider", slider.noUiSlider.get(), 5);
});

var circles_checkbox = document.getElementById("circles_checkbox");
var cylinders_checkbox = document.getElementById("cylinders_checkbox");
var labels_checkbox = document.getElementById("labels_checkbox");
var polylines_checkbox = document.getElementById("polylines_checkbox");

function on_checkbox_click() {
    refresh();
}

//News container

class NewsContainer {
    constructor() {
        this.class = "news_container";
        this.id = "news_container";
        this.createContainer();
    }
    createContainer() {
        "use strict";
        var a = document.createElement("div");
        a.id = this.id;
        a.style.backgroundColor = "rgba(0,0,0,0.9)";
        a.class = this.class;
        a.style.position = "absolute";
        //a.style.padding = "2%";
        a.style.padding = "5px";
        a.style.overflow = "auto";
        //a.style.transition = "opacity 1000ms linear";
        document.getElementById("cesiumContainer").appendChild(a);
        this.container = document.getElementById(this.id);
        return a;
    }
    resizeContainer() {
        "use strict";
        var container = this.container;
        var width = $(window).width();
        var height = $(window).height();
        if (width > height) {
            container.style.right = "1em";
            container.style.left = null;
            container.style.top = "3.9em";
            container.style.bottom = null;
            container.style.maxHeight = "90%";
            container.style.maxWidth = "40%";
        } else {
            container.style.right = "1em";
            container.style.left = "1em";
            container.style.top = null;
            container.style.bottom = "1em";
            container.style.maxHeight = "29%";
            container.style.maxWidth = "100%";
        }
    }
    showContainer() {
        "use strict";
        this.container.hidden = false;
        this.resizeContainer();
    }
    updateContainer(articles, location) {
        "use strict";
        this.container.innerHTML = "";
        var title = document.createElement('p');
        title.innerHTML = location;
        title.className = "containerTitle";
        this.container.appendChild(title);
        var i = 0;
        var thematics = {};
        for (i; i < articles.length; i += 1) {
            var article = null;
            article = articles[i];
            if (article.thematic_number in thematics) {
                thematics[article.thematic_number].push(article);
            } else {
                thematics[article.thematic_number] = [article];
            }
        }
        // Create items array
        var items = Object.keys(thematics).map(function (key) {
                return thematics[key];
            });

        // Sort the array based on the second element
        items.sort(function (first, second) {
            return second.length - first.length;
        });

        thematics = items;

        var whole_list = document.createElement("ul");
        for (var key in thematics) {
            var article_list = thematics[key];
            var thematic_list = document.createElement('ul');
            if (article_list.length > 1) {
                for (var index in article_list) {
                    var child_list = document.createElement("li");
                    var article = article_list[index];
                    if (index == 0) {
                        var theme_name = "\u25b7" + article.title;
                        var span = document.createElement("span");
                        span.className = "Collapsable";
                        span.append(theme_name);
                        thematic_list.append(span);
                    }
                    var a = document.createElement("a");
                    a.innerHTML = "\u26AC " + article.title + '<br>';
                    a.href = article.url;
                    a.style.color = "white";
                    a.style.display = "block";
                    a.style.paddingLeft = "15px";
                    a.className = "Collapsable";
                    a.onclick = save_caches();
                    child_list.appendChild(a);
                    thematic_list.appendChild(child_list);
                }
            } else {
                for (var index in article_list) {
                    var child_list = document.createElement("li");
                    var article = article_list[index];
                    var a = document.createElement("a");
                    a.innerHTML = "\u26AC " + article.title + '<br>';
                    a.href = article.url;
                    a.style.color = "white";
                    a.style.display = "block";
                    a.style.marginTop = "5px";
                    a.onclick = save_caches();
                    child_list.appendChild(a);
                    thematic_list.appendChild(child_list);
                }
            }

            whole_list.appendChild(thematic_list);
        }
        this.container.appendChild(whole_list);

        $(".Collapsable").click(function () {
            $(this).parent().children().toggle();
            $(this).toggle();
        });

        $(".Collapsable").each(function () {
            $(this).parent().children().toggle();
            $(this).toggle();
        });

        this.showContainer();
    }

    hideContainer() {
        "use strict";
        this.container.hidden = true;
    }
}

//Loading container
class LoadingContainer {
    constructor() {
        this.class = "loading_container";
        this.id = "loading_container";
        this.createContainer();
    }
    createContainer() {
        "use strict";
        var a = document.createElement("div");
        a.id = this.id;
        a.style.backgroundColor = "rgba(0,0,0,1)";
        a.class = this.class;
        a.style.position = "absolute";
        //a.style.padding = "2%";
        a.style.overflow = "auto";
        a.style.padding = "5px";
        //a.style.transition = "opacity 1000ms linear";
        document.getElementById("cesiumContainer").appendChild(a);
        this.container = document.getElementById(this.id);
        this.container.innerHTML = "LOADING...";
        this.resizeContainer();
        return a;
    }
    updateContainer(text) {
        this.container.innerHTML = text;
    }
    resizeContainer() {
        "use strict";
        //this.container.style.right = "45%";
        this.container.style.left = "45%";
        this.container.style.top = "45%";
        //this.container.style.bottom = "45%";
        //this.container.style.maxHeight = "10%";
        //this.container.style.maxWidth = "10%";
    }
    showContainer() {
        "use strict";
        //var container = document.getElementById("container");
        this.container.hidden = false;
        this.resizeContainer();
    }
    hideContainer() {
        "use strict";
        //var container = document.getElementById("container");
        this.container.hidden = true;
    }
}

/*
ZOOM BUTTONS
 */
class ZoomContainer {
    constructor() {
        this.id = "zoom_container";
        this.createContainer();
    }
    createContainer() {
        "use strict";
        var a = document.createElement("div");
        a.id = this.id;
        a.style.backgroundColor = "rgba(0,0,0,1)";
        console.log(a.class);
        a.style.position = "absolute";
        //a.style.padding = "2%";
        a.style.overflow = "auto";
        //a.style.padding = "5px";
        a.style.height = "71px";
        a.style.width = "38px";
        a.style.border = "1px";
        a.style.color = "white";
        a.style.backgroundColor = "rgba(0,0,0,0)";
        a.style.borderRadius = "5px";
        //a.style.transition = "opacity 1000ms linear";
        document.getElementsByClassName("cesium-viewer")[0].appendChild(a);
        this.container = document.getElementById(this.id);
        //this.container.innerHTML = "Z";
        var plusButton = document.createElement("div");
        plusButton.className = "cesium-button cesium-toolbar-button noselect";
        plusButton.style.position = "relative";
        plusButton.style.textAlign = "center";
        plusButton.style.verticalAlign = "middle";
        plusButton.style.lineHeight = "31px";
        plusButton.innerHTML = "+";
        plusButton.style.marginBottom="0px";
        plusButton.style.borderBottomLeftRadius = "0px";
        plusButton.style.borderBottomRightRadius = "0px";
        //plusButton.style.cursor = "pointer";
        plusButton.onclick = function() {viewer.camera.zoomIn(0.5*window.height)};
        var minusButton = document.createElement("div");
        minusButton.className = "cesium-button cesium-toolbar-button noselect";
        minusButton.style.position = "relative";
        minusButton.style.width = "32px";
        minusButton.style.height = "31px";
        minusButton.style.textAlign = "center";
        minusButton.style.verticalAlign = "middle";
        minusButton.style.lineHeight = "31px";
        minusButton.innerHTML = "-";
        minusButton.style.borderTopLeftRadius = "0px";
        minusButton.style.borderTopRightRadius = "0px";
        minusButton.style.marginTop="0px";
        //minusButton.style.cursor = "pointer";
        minusButton.onclick = function() {viewer.camera.zoomOut(0.5*window.height)};
        this.container.appendChild(plusButton);
        this.container.appendChild(minusButton);
        this.resizeContainer();
        return a;
    }
    updateContainer(text) {
        this.container.innerHTML = text;
    }
    resizeContainer() {
        "use strict";
        var container = this.container;
        var width = $(window).width();
        var height = $(window).height();
        if (width > height) {
            container.style.right = null;
            container.style.left = "13px";
            container.style.top = null;
            container.style.bottom = "13px";
        } else {
            container.style.right = "5px";
            container.style.left = null;
            container.style.top = "44px";
            container.style.bottom = null;
        }
    }
    showContainer() {
        "use strict";
        //var container = document.getElementById("container");
        this.container.hidden = false;
        this.resizeContainer();
    }
    hideContainer() {
        "use strict";
        //var container = document.getElementById("container");
        this.container.hidden = true;
    }
}

news_container = new NewsContainer();
news_container.hideContainer();
loading_container = new LoadingContainer();
zoom_container = new ZoomContainer();

window.onresize = function () {
    "use strict";
    news_container.resizeContainer();
    loading_container.resizeContainer();
    zoom_container.resizeContainer();
};

//Camera stuff

var scene = viewer.scene;
//scene.debugShowCommands = true;
/*
scene.screenSpaceCameraController.enableTilt = false;
scene.screenSpaceCameraController.enableLook = false;

scene.preRender.addEventListener(function () {
    "use strict";
    scene.fxaa = false;

    viewer.camera.setView({
        orientation : {
            heading : 0,
            pitch : viewer.camera.pitch,
            roll : viewer.camera.roll
        }
    });

});*/

var keyPressed = {};
document.addEventListener('keydown', function (e) {
    "use strict";
    keyPressed[e.keyCode] = true;
    setKey();
}, false);
document.addEventListener('keyup', function (e) {
    "use strict";
    keyPressed[e.keyCode] = false;
}, false);

function setKey() {
    "use strict";
    var horizontalDegrees = 10.0;
    var verticalDegrees = 10.0;
    var viewRect = viewer.camera.computeViewRectangle();
    if (Cesium.defined(viewRect)) {
        horizontalDegrees *= Cesium.Math.toDegrees(viewRect.east - viewRect.west) / 360.0;
        verticalDegrees *= Cesium.Math.toDegrees(viewRect.north - viewRect.south) / 180.0;
    }
    if (keyPressed["116"]) { //F5
        sessionStorage.clear();
    }
    if (keyPressed["16"] && keyPressed["38"]) { //shift+up arrow
        viewer.camera.zoomIn(0.5*window.height);
    } else if (keyPressed["16"] && keyPressed["40"]) { //shift+down arrow
        viewer.camera.zoomOut(0.5*window.height);
    } else if (keyPressed["17"] && keyPressed["39"]) { //ctrl right arrow
        var data = get_closest_neighbour(0);
        selection(data[2]);
    } else if (keyPressed["17"] && keyPressed["37"]) { //ctrl left arrow
        var data = get_closest_neighbour(180);
        selection(data[2]);
    } else if (keyPressed["17"] && keyPressed["38"]) { //ctrl up arrow
        var data = get_closest_neighbour(90);
        selection(data[2]);
    } else if (keyPressed["17"] && keyPressed["40"]) { //ctrl down arrow
        var data = get_closest_neighbour(270);
        selection(data[2]);
    } else if (keyPressed["39"]) { // right arrow
        viewer.camera.rotateRight(Cesium.Math.toRadians(horizontalDegrees));
    } else if (keyPressed["37"]) { // left arrow
        viewer.camera.rotateLeft(Cesium.Math.toRadians(horizontalDegrees));
    } else if (keyPressed["38"]) { // up arrow
        viewer.camera.rotateDown(Cesium.Math.toRadians(verticalDegrees));
    } else if (keyPressed["40"]) { // down arrow
        viewer.camera.rotateUp(Cesium.Math.toRadians(verticalDegrees));
    }
}

function selection(key,fly_to=true) {
    if (key != undefined) {
        var object_articles = window.articles_by_location[key].articles;
        var location_str = window.articles_by_location[key].location;
        if (fly_to == true) {
            viewer.camera.flyTo({
                destination : Cesium.Cartesian3.fromDegrees(
                    articles_by_location[key].lng,
                    articles_by_location[key].lat,
                    window.height),
                duration : 0.5
            });
        }
        window.currentSelectionKey = key;
        news_container.updateContainer(object_articles, location_str);
    }
}

var lastHeight;
var lastStoppedHeight;
var isChanging;
var ellipsoid = viewer.scene.globe.ellipsoid;
window.height = ellipsoid.cartesianToCartographic(scene.camera.position).height;

function save_caches() {
    "use strict";
    var s = save_camera_state();
    save_to_cache("camera_state", s, 5);
    save_to_cache("current_selection", window.currentSelectionKey, 5);

    save_to_cache("get_cylinders",cylinders_checkbox.checked,5);
    save_to_cache("get_circles",circles_checkbox.checked,5);
    //save_to_cache("get_labels",labels_checkbox.checked,5);
    save_to_cache("get_polylines",polylines_checkbox.checked,5);
    save_to_cache("news_container_hidden",news_container.container.hidden);
}

load_caches();

function load_caches() {
    cylinders_checkbox.checked = get_from_cache("get_cylinders",cylinders_checkbox.checked);
    circles_checkbox.checked = get_from_cache("get_circles",circles_checkbox.checked);
    //labels_checkbox.checked = get_from_cache("get_labels",labels_checkbox.checked);
    polylines_checkbox.checked = get_from_cache("get_polylines",polylines_checkbox.checked);

    var current_selection_cache = get_from_cache("current_selection",undefined);

    if (current_selection_cache != undefined) {
        window.current_selection = current_selection_cache;
    }
    else {
        help_button.click();
    }

    news_container.container.hidden = get_from_cache("news_container_hidden",news_container.container.hidden);
    
    load_camera_cache();
    s = get_from_cache("slider");

    if (s != null) {
        slider.noUiSlider.set(s);
    }
}


function load_camera_cache() {
    var loaded = get_from_cache("camera_state");
    if (loaded != null) {
        load_camera_state(loaded);
        //refresh?
    }
}

function save_camera_state() {
    "use strict";
    var state = {
        position : viewer.camera.position,
        direction : viewer.camera.direction,
        up : viewer.camera.up,
        right : viewer.camera.right,
        //transform : viewer.camera.transform
        //frustum: camera.frustum.clone(),
    };
    return JSON.parse(JSON.stringify(state));;
}

function load_camera_state(state) {
    "use strict";
    viewer.camera.position = state.position;
    viewer.camera.direction = state.direction;
    viewer.camera.up = state.up;
    viewer.camera.right = state.right;
    //viewer.camera.transform = state.transform;
}

// Object selecton and movement
var handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);

window.currentlySelected = null;
window.currentSelectionKey = null;

handler.setInputAction(function (movement) {
    "use strict";
    var pickedObject = scene.pick(movement.position);
    //Code that doesnt let picking across (through) earth
    if(pickedObject != undefined) {
        if ("_position" in pickedObject.primitive) {
            var picked_object_position = pickedObject.primitive._position;
            var ellipsoid_pick_cartesian = viewer.camera.pickEllipsoid(movement.position);
            var camera_pos = viewer.camera.position;
            if (ellipsoid_pick_cartesian != undefined) {
                var distance_camera_to_ellipsoid = Cesium.Cartesian3.distance(camera_pos,ellipsoid_pick_cartesian);
                var distance_camera_to_object = Cesium.Cartesian3.distance(camera_pos,picked_object_position);
                if (distance_camera_to_ellipsoid < distance_camera_to_object) {
                    pickedObject = undefined;
                }
            }
        }
    }
    if (pickedObject != undefined) {
        window.currentlySelected = pickedObject;
        var key = pickedObject.id;
        selection(key);
    } else {
        window.currentlySelected = null;
        news_container.hideContainer();
    }

}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

handler.setInputAction(function (movement) {
    "use strict";
    viewer.trackedEntity = undefined;
}, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);

function get_closest_neighbour(angle_final) {
    "use strict";
    var origin_key_splitted = window.currentSelectionKey.split(',');
    var lat_origin = parseFloat(origin_key_splitted[0]);
    var lng_origin = parseFloat(origin_key_splitted[1]);
    var neighbours = [];
    Object.keys(window.articles_by_location).forEach(function (key) {
        var splitted = key.split(',');
        var lat = parseFloat(splitted[0]);
        var lng = parseFloat(splitted[1]);
        var distance = getDistanceFromLatLonInKm(lat_origin, lng_origin, lat, lng);
        var angle = 90 - bearing(lat_origin, lng_origin, lat, lng);
        //var distance = Math.sqrt(lat_moved ^ 2 + lng_moved ^ 2);
        neighbours.push([distance, angle, key, window.articles_by_location[key].location]);
    });
    var angle = angle_final % 360;
    var angle_min = normalize_angle(angle - 60);
    var angle_max = normalize_angle(angle + 60);
    var to_sort = [];

    Object.keys(neighbours).forEach(function (n) {
        var distance = neighbours[n][0];
        var angle_to_neighbour = neighbours[n][1];
        if (distance == 0) {
            to_sort.push(neighbours[n]);
        } else if (angle_within_limits(angle_min, angle_max, angle_to_neighbour)) {
            to_sort.push(neighbours[n]);
        }

    });
    var compared = to_sort.sort(Comparator);
    return compared[1];
}

function radians(n) {
    return n * (Math.PI / 180);
}

function degrees(n) {
    return n * (180 / Math.PI);
}

function bearing(startLat, startLong, endLat, endLong) {
    startLat = radians(startLat);
    startLong = radians(startLong);
    endLat = radians(endLat);
    endLong = radians(endLong);

    var dLong = endLong - startLong;

    var dPhi = Math.log(Math.tan(endLat / 2.0 + Math.PI / 4.0) / Math.tan(startLat / 2.0 + Math.PI / 4.0));
    if (Math.abs(dLong) > Math.PI) {
        if (dLong > 0.0)
            dLong =  - (2.0 * Math.PI - dLong);
        else
            dLong = (2.0 * Math.PI + dLong);
    }

    return (degrees(Math.atan2(dLong, dPhi)) + 360.0) % 360.0;
}

function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
    var R = 6371; // Radius of the earth in km
    var dLat = radians(lat2 - lat1); // radians below
    var dLon = radians(lon2 - lon1);
    var a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(radians(lat1)) * Math.cos(radians(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var d = R * c; // Distance in km
    return d;
}

function normalize_angle(angle) {
    "use strict";
    while (angle < 0) {
        angle += 360;
    }
    return angle % 360;
}

function angle_within_limits(min, max, N) {
    "use strict";
    min = normalize_angle(min);
    max = normalize_angle(max);
    N = normalize_angle(N);
    if (min == max) {
        if (N == min && N == max) {
            return true;
        }
    }
    if (min > max) {
        max += 360;
        if (N < min) {
            N += 360;
        }
    }
    if (N <= max && N >= min) {
        return true;
    }
    return false;
}

function Comparator(a, b) {
    "use strict";
    if (a[0] < b[0]) {
        return -1;
    }
    if (a[0] > b[0]) {
        return 1;
    }
    if (a[1] < b[1]) {
        return -1;
    }
    if (a[1] > b[1]) {
        return 1;
    }
    return 0;
}

function get_diff(a, b) {
    "use strict";
    if (a > b) {
        return a - b;
    }
    return b - a;
}

//Entities

function getArticlesInRange(articles) {
    "use strict";
    var out = {};
    var keys = Object.keys(articles);
    var i = 0;
    for (i; i < keys.length; i += 1) {
        var key = keys[i];
        var articles_per_location = articles[key].articles;
        var j = 0;
        for (j; j < articles_per_location.length; j += 1) {
            var time = Date.parse(articles_per_location[j].publishedAt);
            if (isTimeWithinLimits(time)) {
                var article = articles_per_location[j];
                //article.time_percentage = getTimePercentage(time);
                var time_percentage = getTimePercentage(time);
                if (key in out) {
                    out[key].articles.push(article);
                    out[key].count += 1;
                    if (time_percentage > out[key].time_percentage) {
                        out[key].time_percentage = time_percentage; //if bigger
                    }
                } else {
                    out[key] = {};
                    out[key].location = articles[key].location;
                    out[key].lat = articles[key].lat;
                    out[key].lng = articles[key].lng;
                    out[key].articles = [article];
                    out[key].count = 1;
                    out[key].time_percentage = time_percentage;
                }
            }
        }
    }
    return out;
}

window.schedule_refresh_after_touch = false;
window.primitives = new Cesium.PrimitiveCollection();
window.articles_by_location = {};
window.zoom_changing = false;


function drawCircles() {
    "use strict";
    //window.primitives.destroy();
    //window.primitives_old = window.primitives;
    for (var i = 0; i < window.primitives.length; i += 1) {
        window.primitives[i].destroy();
    }
    window.primitives = createPrimitives({
            get_cylinders : cylinders_checkbox.checked,
            get_circles : circles_checkbox.checked,
            get_labels : false,
            get_polylines : polylines_checkbox.checked
        });
    for (var i = 0; i < window.primitives.length; i += 1) {
        scene.primitives.add(window.primitives[i]);
    }
    //window.primitives_old.removeAll();
    //loading_container.hideContainer();
}

var counted_articles = null;
//getArticlesCounted();
download_articles();

function download_articles() {
    getArticlesCounted();
    /*
    //THIS FUNCTIONALITY APPEARS TO BE BROKEN
    var time = (new Date()).getTime();
    var time_of_creation_from_txt = null;
    $.ajax({
            url : "time.txt" + "?nocache=" + time,
            //data: data,
            success : function (result) {
                time_of_creation_from_txt = result;
            },
            dataType : "text",
            type : 'GET',
            mimeType : "application/octet-stream; charset=x-user-defined"
        }).done(function () {
            time_of_creation_from_cache = get_from_cache("creation_time");
            if (time_of_creation_from_cache == null) {
                console.log("No cached time was available.")
                getArticlesCounted();
                save_to_cache("creation_time",time_of_creation_from_txt,60*24);
            }
            else {
                if (time_of_creation_from_txt > time_of_creation_from_cache) {
                    console.log("New articles file available! Removing cached version...")
                    remove_from_cache("counted_articles");
                    save_to_cache("creation_time",time_of_creation_from_txt,60*24);
                    getArticlesCounted();
                }
                else {
                    console.log("No changes on server...");
                    getArticlesCounted();
                }
            }

        }).fail(function () {
            getArticlesCounted();
        });
    */
}


function getArticlesCounted() {
    "use strict";
    var coordList;
    var time = (new Date()).getTime();
    var cached = get_from_cache("counted_articles");
    loading_container.updateContainer("Loading articles...");
    if (cached == null) {
        loading_container.updateContainer("Downloading articles...")
        $.ajax({
            url : "counted_by_location" + "?nocache=" + time,
            //data: data,
            success : function (result) {
                var result_out = pako.inflate(result, {
                        to : 'string'
                    });
                var json = JSON.parse(result_out);
                counted_articles = json;
            },
            dataType : "text",
            type : 'GET',
            mimeType : "application/octet-stream; charset=x-user-defined"
        }).done(function () {
            console.log("Counted articles loaded!");
            loading_container.hideContainer();
            refresh();
            selection(get_from_cache("current_selection",undefined),false);
            save_to_cache("counted_articles", counted_articles, 60);
        }).fail(function () {
            console.log("Counted articles failed to load!");
        });
    } else {
        counted_articles = cached;
        loading_container.hideContainer();
        refresh();
        selection(get_from_cache("current_selection",undefined),false);
    }
}

window.height = ellipsoid.cartesianToCartographic(scene.camera.position).height;

function createCircle(lat, lng, id, count, color_code) {
    "use strict";
    color_code.alpha = 0.8;
    var radius = erf(window.height / 3e6) * Math.log(count + 1.5) * 11e4;
    var circleInstance = new Cesium.GeometryInstance({
            geometry : new Cesium.CircleGeometry({
                center : Cesium.Cartesian3.fromDegrees(lng, lat),
                radius : radius,
                vertexFormat : Cesium.PerInstanceColorAppearance.VERTEX_FORMAT
            }),
            attributes : {
                color : Cesium.ColorGeometryInstanceAttribute.fromColor(color_code)
            },
            id : id
        });
    return circleInstance;
}

function createCylinder(lat, lng, id, count, height, color_code) {
    "use strict";

    color_code.alpha = 1.0;
    var radius = erf(window.height / 3e6) * Math.log(count + 1.5) * 2e4;
    if (height > window.height) {
        height = window.height - 1e4;
    }
    var cyl_geometry = new Cesium.CylinderGeometry({
            topRadius : radius,
            bottomRadius : radius,
            length : height,
            vertexFormat : Cesium.PerInstanceColorAppearance.VERTEX_FORMAT,
        });
    var cylinder = new Cesium.GeometryInstance({
            geometry : cyl_geometry,
            modelMatrix : Cesium.Matrix4.multiplyByTranslation(Cesium.Transforms.eastNorthUpToFixedFrame(
                    Cesium.Cartesian3.fromDegrees(lng, lat)), new Cesium.Cartesian3(0.0, 0.0, height * 0.5), new Cesium.Matrix4()),
            attributes : {
                color : Cesium.ColorGeometryInstanceAttribute.fromColor(color_code)
            },
            id : id
        });
    return cylinder;
}

function createPrimitives({
    get_cylinders = true,
    get_circles = true,
    get_labels = true,
    get_polylines = true
}
         = {}) {
    var collection = new Cesium.PrimitiveCollection();
    var keys = Object.keys(window.articles_by_location);
    var i = 0;
    var instances_circle = [];
    var instances_cylinder = [];
    var labels = new Cesium.LabelCollection();
    var polylines = new Cesium.PolylineCollection();
    for (i; i < keys.length; i += 1) {
        var key = keys[i];
        var lat = window.articles_by_location[key].lat;
        var lng = window.articles_by_location[key].lng;
        var count = window.articles_by_location[key].count;
        var height = 100000 * count;
        var loc = window.articles_by_location[key].location;
        var time_percentage = window.articles_by_location[key].time_percentage;
        var color = new Cesium.Color.fromCssColorString("#" + rainbow.colorAt(time_percentage * 100));

        if (get_cylinders) {
            var cylinders = createCylinder(lat, lng, key, count, height, color);
            instances_cylinder.push(cylinders);
        }
        if (get_circles) {
            var circles = createCircle(lat, lng, key, count, color);
            instances_circle.push(circles);
        }
        if (get_labels) {
            if (get_cylinders || get_polylines) {
                var height_label = height + 1e4;
            } else {
                var height_label = 1e5;
            }
            labels.add({
                position : new Cesium.Cartesian3.fromDegrees(lng, lat, height_label),
                text : loc,
                //font : "12px sans-serif",
                horizontalOrigin : 0, // 0 means center
                verticalOrigin : 0, // o means center
                id : key,
                //showBackground : true,
                outlineWidth : 3.0,
                //backgroundColor : new Cesium.Color(0, 0, 0, 0),
                style : Cesium.LabelStyle.FILL_AND_OUTLINE
            });
        }
        if (get_polylines) {
            polylines.add({
                positions : [new Cesium.Cartesian3.fromDegrees(lng, lat, 0), new Cesium.Cartesian3.fromDegrees(lng, lat, height + 1e4)],
                width : 10,
                id : key,
                material : new Cesium.Material.fromType('Color', {
                    color : color
                })
            });
        };
    }
    var primitives_cylinders = new Cesium.Primitive({
            geometryInstances : instances_cylinder,
            appearance : new Cesium.PerInstanceColorAppearance({
                translucent : false,
                //closed: true
            }),
        });
    var primitives_circle = new Cesium.Primitive({
            geometryInstances : instances_circle,
            appearance : new Cesium.PerInstanceColorAppearance({
                //translucent: false,
                //closed: true
            }),
        });
    return [primitives_cylinders, primitives_circle, labels, polylines];
}

window.touch = false;
//window.number_of_touches = 0;
$(document).on('touchstart', function (event) {
    window.touch = true;
    //window.number_of_touches = event.touches.length;
});

$(document).on('touchend', function (event) {
    window.touch = false;
    //window.number_of_touches = 0;
    if (window.schedule_refresh_after_touch == true) {
        window.schedule_refresh_after_touch = false;
        drawCircles();
    }
});

function refresh() {
    "use strict";
    window.articles_by_location = getArticlesInRange(counted_articles);
    drawCircles();
    
    scene.preRender.addEventListener(function () {
        window.height = ellipsoid.cartesianToCartographic(scene.camera.position).height;
        if (lastHeight !== window.height) {
            //Camera height has changed
            window.clearTimeout(isChanging);
            window.zoom_changing = true;
            lastHeight = window.height;
            isChanging = setTimeout(function () {
                    //Zooming stopped
                    window.zoom_changing = false;
                    if (Math.abs(lastStoppedHeight - lastHeight) > 1e6) {
                        if (window.touch == false) {
                            if (circles_checkbox.checked || cylinders_checkbox.checked) {
                                drawCircles();
                            }
                        } else {
                            window.schedule_refresh_after_touch = true;
                        }
                    }
                    lastStoppedHeight = lastHeight;
                }, 100);
        }
    });
}

//UTILITIES


function save_to_cache(name, object, expires_minutes = 15) {
    /*
    expires_minutes takes minutes until expiration
     */
    var currentDate = new Date();
    expires = new Date(currentDate.getTime() + expires_minutes * 60000); //15 minutes

    var sessionObject = {
        expiresAt : expires,
        object : object
    };
    out_object = JSON.stringify(sessionObject);
    sessionStorage.setItem(name, out_object);
}

function get_from_cache(name,default_return=null) {
    var currentDate = new Date();
    var sessionObject = JSON.parse(sessionStorage.getItem(name));
    if (sessionObject == null) {
        return default_return;
    } else {
        var expirationDate = sessionObject.expiresAt;
        if (Date.parse(currentDate) < Date.parse(expirationDate)) {
            return sessionObject.object;
        } else {
            sessionStorage.removeItem(name);
            return default_return;
        }
    }
}

function remove_from_cache(name) {
    sessionStorage.removeItem(name);
}

function isTimeWithinLimits(time) {
    "use strict";
    if (time >= window.timeFrom) {
        if (time < window.timeTo) {
            return true;
        }
    }
    return false;
}

function getTimePercentage(time) {
    percentage = (time - window.timeFrom) / (window.timeTo - window.timeFrom);
    return percentage;
}

function float_2_str(lat, lng, precision) {
    "use strict";
    return String(lat.toFixed(precision)) + "," + String(lng.toFixed(precision));
}

function erf(x) {
    // constants
    "use strict";
    var a1 = 0.254829592;
    var a2 = -0.284496736;
    var a3 = 1.421413741;
    var a4 = -1.453152027;
    var a5 = 1.061405429;
    var p = 0.3275911;

    // Save the sign of x
    var sign = 1;
    if (x < 0) {
        sign = -1;
    }
    x = Math.abs(x);

    // A&S formula 7.1.26
    var t = 1.0 / (1.0 + p * x);
    var y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
}

function date_to_str(dateObj) {
    "use strict";
    var month = dateObj.getUTCMonth() + 1; //months from 1-12
    var day = dateObj.getUTCDate();
    var year = dateObj.getUTCFullYear();
    return year + "-" + month + "-" + day;
}

