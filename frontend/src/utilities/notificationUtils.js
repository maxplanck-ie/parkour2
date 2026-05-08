import { h } from "vue";
import { useToast } from "vue-toastification";

const toast = useToast();

export function showNotification(content, type, customOptions = {}) {
  let options = {
    timeout: 5000,
    position: "top-left",
    ...customOptions
  };

  if (type === "info") toast.info(content, options);
  else if (type === "success") toast.success(content, options);
  else if (type === "error") toast.error(content, options);
  else if (type === "warning") toast.warning(content, options);
}

export function showUndoNotification(content, onUndo, options = {}) {
  if (typeof onUndo !== "function") {
    showNotification(content, options.type || "success", options);
    return null;
  }

  const notificationOptions = {
    timeout: 10000,
    position: "top-left",
    closeOnClick: false,
    draggable: false,
    type: options.type || "success",
    ...options
  };

  let toastId = null;
  let undoInProgress = false;
  const onUndoClick = async (event) => {
    event?.stopPropagation?.();
    if (undoInProgress) {
      return;
    }
    undoInProgress = true;

    if (toastId !== null && toastId !== undefined) {
      toast.dismiss(toastId);
      toastId = null;
    }

    try {
      await onUndo();
    } finally {
      undoInProgress = false;
    }
  };

  toastId = toast(
    h("div", { class: "undo-toast-content" }, [
      h("span", { class: "undo-toast-message" }, content),
      h(
        "button",
        {
          type: "button",
          class: "undo-toast-button",
          onClick: onUndoClick
        },
        "Undo"
      )
    ]),
    notificationOptions
  );

  return toastId;
}
