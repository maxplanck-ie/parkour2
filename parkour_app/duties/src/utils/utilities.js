export function showNotification(content, type) {
    console.log(content)
}

export function handleError(error) {
  if (error.response) {
    console.log("Error status:", error.response.status);
    console.log("Error data:", error.response.data);
  } else if (error.request) {
    console.log("No response received. The request may have timed out.");
  } else {
    console.log("Error:", error.message);
  }
}

export function getProp(object, keys, defaultVal) {
  keys = Array.isArray(keys) ? keys : keys.split(".");
  object = object[keys[0]];
  if (object && keys.length > 1) {
    return getProp(object, keys.slice(1), defaultVal);
  }
  return object === undefined ? defaultVal : object;
}
