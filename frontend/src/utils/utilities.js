import { useToast } from "vue-toastification";

const toast = useToast();

export function showNotification(content, type) {
  let options = {
    timeout: 3000,
    toastClassName: "toast-main",
    bodyClassName: "toast-body",
    containerClassName: "toast-container"
  };
  if (type === "info") toast.info(content, options);
  else if (type === "success") toast.success(content, options);
  else if (type === "error") toast.error(content, options);
  else if (type === "warning") toast.warning(content, options);
}

export function handleError(error) {
  if (error.response.status && error.response.status === 403) {
    let slices = window.location.href.split("/vue/");
    window.location.href =
      urlStringStartsWith() + "/login/?next=/vue/" + slices[1];
  } else if (error.response) {
    showNotification("Error:" + error.response.data, "error");
    console.log("Error status:", error.response.status);
    console.log("Error data:", error.response.data);
  } else if (error.request) {
    showNotification(
      "No response received. The request may have timed out.",
      "error"
    );
    console.log("No response received. The request may have timed out.");
  } else {
    showNotification("Error: " + error.message, "error");
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

export function urlStringStartsWith() {
  let urlString = window.location.href.split("/vue/");
  if (urlString[0] === "http://localhost:5174") {
    return "http://localhost:9980";
  } else {
    return urlString[0];
  }
}
