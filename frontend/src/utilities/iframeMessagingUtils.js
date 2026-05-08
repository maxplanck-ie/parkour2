let parentMessageBridgeInitialized = false;

function dispatchSyntheticDocumentInteraction() {
  if (typeof document === "undefined") {
    return;
  }

  const target = document.body || document;
  const baseInit = {
    bubbles: true,
    cancelable: true,
    view: window
  };

  if (window.PointerEvent) {
    const pointerEvent = new PointerEvent("pointerdown", {
      ...baseInit,
      pointerType: "mouse",
      isPrimary: true
    });
    target.dispatchEvent(pointerEvent);
  } else {
    const mouseDownEvent = new MouseEvent("mousedown", baseInit);
    target.dispatchEvent(mouseDownEvent);
  }

  const clickEvent = new MouseEvent("click", baseInit);
  target.dispatchEvent(clickEvent);
}

function handleParentMessage(event) {
  if (
    !event ||
    event.origin !== window.location.origin ||
    !event.data ||
    event.data.source !== "mainhub-ext"
  ) {
    return;
  }

  if (event.data.type === "parent-pointer-down") {
    dispatchSyntheticDocumentInteraction();
  }
}

export function initParentMessageBridge() {
  if (typeof window === "undefined" || parentMessageBridgeInitialized) {
    return;
  }

  window.addEventListener("message", handleParentMessage);
  parentMessageBridgeInitialized = true;
}
