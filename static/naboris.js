var arrow_keys = [33,34,35,36,37,38,39,40];

$(document).keydown(function(e) {
     var key = e.which;
      //console.log(key);
      //if(key==35 || key == 36 || key == 37 || key == 39)
      if($.inArray(key, arrow_keys) > -1) {
          e.preventDefault();
          return false;
      }
      return true;
});

// Only run what comes next *after* the page has loaded
addEventListener("DOMContentLoaded", function() {
    // Grab all of the elements with a class of command
    // (which all of the buttons we just created have)
    var commandButtons = document.querySelectorAll(".command_button");

    for (var i = 0; i < commandButtons.length; i++)
    {
        var button = commandButtons[i];

        // For each button, listen for the "click" event
        button.addEventListener("click", function(e) {
            // When a click happens, stop the button
            // from submitting our form (if we have one)
            e.preventDefault();

            var clickedButton = e.target;
            var command = clickedButton.value;

            requestCommand(command, clickedButton);
        });
    }
}, true);


var motors_moving = false;
var looking = false;
let default_speed = 75;
let default_lateral = 150;
var increment = 0;
let amount = 4;

document.onkeydown = checkKeyDown;
document.onkeyup = checkKeyUp;

function checkKeyDown(e) {
    e = e || window.event;

    if (e.keyCode == '38') {
        // up arrow
        requestCommand("d_0_" + limitSpeed(default_speed + increment));
        motors_moving = true;
        increment += amount;
    }
    else if (e.keyCode == '40') {
        // down arrow
        requestCommand("d_180_" + limitSpeed(default_speed + increment));
        motors_moving = true;
        increment += amount;
    }
    else if (e.keyCode == '37') {
       // left arrow
       requestCommand("l_" + limitSpeed(default_speed + increment));
       motors_moving = true;
       increment += amount;
    }
    else if (e.keyCode == '39') {
       // right arrow
       requestCommand("r_" + limitSpeed(default_speed + increment));
       motors_moving = true;
       increment += amount;
    }
    else if (e.keyCode == '87') {
        // w
       requestCommand("d_0_" + limitSpeed(default_speed + increment));
       motors_moving = true;
       increment += amount;
    }
    else if (e.keyCode == '83') {
        // s
       requestCommand("d_180_" + limitSpeed(default_speed + increment));
       motors_moving = true;
       increment += amount;
    }
    else if (e.keyCode == '68') {
        // d
       requestCommand("d_270_" + limitSpeed(default_lateral + increment));
       motors_moving = true;
       increment += amount;
    }
    else if (e.keyCode == '65') {
        // a
       requestCommand("d_90_" + limitSpeed(default_lateral + increment));
       motors_moving = true;
       increment += amount;
    }

    else if (e.keyCode == '79') {
        // o
        requestCommand(":toggle_lights", document.getElementById("toggle_lights_button"));
    }

    if (!looking)
    {
        if (e.keyCode == '73') {
            // i
            requestCommand("look_up");
            looking = true;
        }
        else if (e.keyCode == '75') {
            // k
            requestCommand("look_down");
            looking = true;
        }
        else if (e.keyCode == '74') {
            // j
            requestCommand("look_left");
            looking = true;
        }
        else if (e.keyCode == '76') {
            // l
            requestCommand("look_right");
            looking = true;
        }
    }
}

function limitSpeed(speed) {
    if (speed > 255) {
        speed = 255;
    }
    if (speed < 0) {
        speed = 0;
    }
    console.log(speed);
    return speed;
}

function checkKeyUp(e) {
    e = e || window.event;

    if (motors_moving) {
        motors_moving = false;
        increment = 0;
        requestCommand("s");
    }
    else if (looking) {
        requestCommand("look");
        looking = false;
    }
}


function requestCommand(command, clickedButton=null) {
    // Now we need to send the data to our server
    // without reloading the page - this is the domain of
    // AJAX (Asynchronous JavaScript And XML)
    // We will create a new request object
    // and set up a handler for the response
    var request = new XMLHttpRequest();

    request.onload = function() {
        // alert(request.responseText);

        if (request.responseText.length > 0) {
            clickedButton.innerHTML = request.responseText;
            // clickedButton.value <- change sent command
        }
    };

    // We point the request at the appropriate command
    request.open("POST", "/cmd?command=" + command, true);

    // and then we send it off
    request.send();
}


function myInsertAndExecute(id, text)
{
    domelement = document.getElementById(id);
    domelement.innerHTML = text;
    var scripts = [];

    ret = domelement.childNodes;
    for (var i = 0; ret[i]; i++) {
      if (scripts && myNodeName(ret[i], "script") && (!ret[i].type || ret[i].type.toLowerCase() === "text/javascript")) {
            scripts.push(ret[i].parentNode ? ret[i].parentNode.removeChild(ret[i]) : ret[i]);
        }
    }

    for(script in scripts)
    {
      myEvalScript(scripts[script]);
    }
}
function myNodeName(elem, name) {
    return elem.nodeName && elem.nodeName.toUpperCase() === name.toUpperCase();
}

function myEvalScript(elem)
{
    data = (elem.text || elem.textContent || elem.innerHTML || "");

    var head = document.getElementsByTagName("head")[0] || document.documentElement;
    script = document.createElement("script");
    script.type = "text/javascript";
    script.appendChild(document.createTextNode(data));
    head.insertBefore(script, head.firstChild);
    head.removeChild(script);

    if (elem.parentNode) {
        elem.parentNode.removeChild(elem);
    }
}


function requestAngle() {
    var request = new XMLHttpRequest();
    request.open("GET", "/angle", true);
    request.responseType = "text/plain";
    request.setRequestHeader("Content-type", "text/plain")
    request.send();

    var timer;
    var position = 0;
    timer = setInterval(function() {
        if (request.responseText.length > 0) {
            // check the response for new data

            angle_message = request.responseText.split("\n")
            for (i = 0; i < angle_message.length; i++) {
                if (angle_message[i].length > 0) {
                    angle = parseInt(angle_message[i]);
                    setCompassDirection(angle);
                }
            }
        }
            // stop checking once the response has ended
        if (request.readyState == XMLHttpRequest.DONE) {
            clearInterval(timer);
        }

    }, 50);
}

initCompass();
requestAngle();

/*
function handlePlot(data) {
//    var graph = $("#container");
//    graph.html(data);
//    document.getElementById("container").innerHTML = "something interesting";
    myInsertAndExecute("container", data);
}


function requestPlot() {
    var request = new XMLHttpRequest();
    request.open("POST", "/plot", true);
    request.responseType = "html";
    request.setRequestHeader("Content-type", "application/json; charset=utf-8")
    request.send();

    var timer;
    var position = 0;
    timer = setInterval(function() {
        if (request.responseText.length > 0) {
            // check the response for new data
            message = request.responseText.split("<style>\n\n</style>\n").slice(-1).pop();
//            console.log(messages.length);
            handlePlot(message);
//            console.log(messages);
//            messages.slice(position, -1).forEach(function(value) {
//                handlePlot(value);
//            });
//            console.log(request.responseText);
//            position = messages.length - 1;
        }
            // stop checking once the response has ended
        if (request.readyState == XMLHttpRequest.DONE) {
            clearInterval(timer);
        }

    }, 50);
}
*/
