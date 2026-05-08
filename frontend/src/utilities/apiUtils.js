import axios from "axios";
import Cookies from "js-cookie";
import { showNotification } from "./notificationUtils";

function notifyParentAuthRequired() {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(
        {
          source: "mainhub-vue",
          type: "auth-required"
        },
        window.location.origin
      );
    }
  } catch (error) {
    // No-op: notification is a best-effort signal.
  }
}

export function handleError(error) {
  if (
    error.response &&
    error.response.status &&
    error.response.status === 403
  ) {
    let slices = window.location.href.split("/vue/");
    notifyParentAuthRequired();
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
