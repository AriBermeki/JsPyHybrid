let EventRegistry = {};
EventRegistry.clientRegisteredFunctions = {};
EventRegistry.pythonFunctionNamespace = new Map();
EventRegistry.functionResponse = null;
EventRegistry.socket = null;

EventRegistry.initialize = function () {
    if (window.location.protocol === 'http:') {
        //EventRegistry.socket= io('ws://' + `${window.location.host }` , { path: `${EventRegistry.socket_path_prefix}`+`${EventRegistry.socket_mount_location}socket.io`, transports: ['websocket', 'polling']});
        EventRegistry.socket= io(`ws://${window.location.host }`, { path: "/hybrid/socket.io/", transports: ['websocket', 'polling']});
    } else if (window.location.protocol === 'https:') {
        //EventRegistry.socket= io('wss://' + `${window.location.host }` , { path: `${EventRegistry.socket_path_prefix}`+`${EventRegistry.socket_mount_location}socket.io`, transports: ['websocket', 'polling']});
        EventRegistry.socket= io(`wss://${window.location.host }`, { path: "/hybrid/socket.io/", transports: ['websocket', 'polling']});
    } else {
        EventRegistry.socket= null;
    }
    
    // Set up socket event handlers
    EventRegistry.socket.on('connect', () => {
      console.log('WebSocket connection established.');
    });
  
    EventRegistry.socket.on('disconnect', () => {
      console.log('WebSocket connection closed.');
    });
  
    EventRegistry.socket.on('call_javascript_func', (data) => {
      EventRegistry.callRegisteredFunction(data);
      console.log('Received call_javascript_func from server:', data);
    });
  
    EventRegistry.socket.on('server_respons', (data) => {
      console.log(data);
      EventRegistry.handleResponse(data);
    });
  };
  

EventRegistry.registerFunction = function (funcName, callback) {
  this.clientRegisteredFunctions[funcName] = callback;
};

EventRegistry.callRegisteredFunction = function (data) {
  const parse = JSON.parse(data);
  const funcName = parse.func_name;
  const args = parse.args;

  if (this.clientRegisteredFunctions[funcName]) {
    this.clientRegisteredFunctions[funcName](...args);
  } else {
    console.error(`Function ${funcName} is not registered on the client.`);
  }
};

EventRegistry.pyFunction = function (funcName, args = []) {
  const request = {
    func_name: funcName,
    args: args
  };
  this.pythonFunctionNamespace.set(funcName, funcName);
  this.socket.emit('call_server_function', request);
};

EventRegistry.handleResponse = function (data) {
  if (data.func_name) {
    console.log('handleResponse ' + ': ' + data.func_name);
    const funcName = data.func_name;
    const result = data.result;
    if (this.pythonFunctionNamespace.has(funcName)) {
      console.log('hallo');
      this.functionResponse = result;
    }
  } else {
    return data;
  }
};

EventRegistry.pyFunctionReturn = function (func_name) {
  if (this.pythonFunctionNamespace.has(func_name)) {
    return this.functionResponse;
  }
};

EventRegistry.function_response = async function (params) {
  return params;
};

EventRegistry.async_spawn = function (spawn_container, func) {
  this.EventRegistry.socket.on('spawn_message', (data) => {
    const container = document.getElementById(spawn_container);
    container.textContent = data.result;
    func(data.result)
  });
};



EventRegistry.initialize()
if(typeof require !== 'undefined'){
    // Avoid name collisions when using Electron, so jQuery etc work normally
    window.nodeRequire = require;
    delete window.require;
    delete window.exports;
    delete window.module;
}
