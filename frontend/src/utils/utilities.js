import { useToast } from "vue-toastification";
import axios from "axios";
import Cookies from "js-cookie";

const toast = useToast();

export function showNotification(content, type) {
  let options = {
    timeout: 5000,
    position: "top-right"
  };

  if (type === "info") toast.info(content, options);
  else if (type === "success") toast.success(content, options);
  else if (type === "error") toast.error(content, options);
  else if (type === "warning") toast.warning(content, options);
}

export function handleError(error) {
  if (
    error.response &&
    error.response.status &&
    error.response.status === 403
  ) {
    let slices = window.location.href.split("/vue/");
    window.location.href =
      urlStringStartsWith() + "/login/?next=/vue/" + slices[1];
  } else if (error.message) {
    showNotification("Error: " + error.message, "error");
  } else {
    showNotification(
      "An error occurred while processing your request.\nPlease contact the BioInfo department for assistance.",
      "error"
    );
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

export function createAxiosObject() {
  return axios.create({
    withCredentials: true,
    headers: {
      "content-type": "application/json",
      "X-CSRFToken": Cookies.get("csrftoken")
    }
  });
}
