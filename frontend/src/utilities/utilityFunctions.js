import { useToast } from "vue-toastification";
import axios from "axios";
import Cookies from "js-cookie";

const toast = useToast();

export function showNotification(content, type) {
  let options = {
    timeout: 5000,
    position: "top-left",
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
      "X-CSRFToken": Cookies.get("csrftoken"),
    },
  });
}

export function isValidDate(dateString) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return false;
  const [yearStr, monthStr, dayStr] = dateString.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  if (year < 1000 || year > 9999) return false;
  if (month < 1 || month > 12) return false;
  if (day < 1 || day > 31) return false;
  const date = new Date(dateString);
  return (
    date.getFullYear() === year &&
    date.getMonth() + 1 === month &&
    date.getDate() === day
  );
}

export function formatDateForInput(date) {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDisplayDate(date) {
  if (!date) return "";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}.${month}.${year}`;
}

export function ellipsisContainer(text, boldText) {
  return `<div title='${text}' style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 12px 8px 12px 12px; font-weight: ${
    boldText === true ? "bold" : "normal"
  }">
                ${text}
              </div>`;
}

export function cellContextMenu(
  allowCopy,
  allowPaste,
  allowApplyToAll,
  getTabulatorInstance
) {
  const tabulatorInstance = getTabulatorInstance();
  const operations = [];
  let isRangeSelected = false;
  let selectedRangesData = tabulatorInstance.getTable().getRangesData();
  if (selectedRangesData.length > 0) {
    let firstRangeFields = Object.keys(selectedRangesData[0][0]);
    isRangeSelected =
      selectedRangesData[0].length > 1 || firstRangeFields.length > 1;
  }

  if (isRangeSelected) {
    showNotification(
      "Please use Ctrl+C to copy, and Ctrl+V to paste in a range selection.",
      "info"
    );
  } else {
    if (allowApplyToAll) {
      operations.push({
        label: "Apply to All",
        action: (e, cell) => {
          const value = cell.getValue();
          const field = cell.getField();
          const libraryProtocolName = cell
            .getRow()
            .getData().library_protocol_name;
          tabulatorInstance
            .getTable()
            .getRows()
            .forEach((row) => {
              if (row.getData().library_protocol_name === libraryProtocolName) {
                const targetCell = row.getCell(field);
                if (
                  !targetCell.getElement().classList.contains("disable-editing")
                ) {
                  targetCell.setValue(value);
                }
              }
            });
        },
      });
    }

    if (allowCopy) {
      operations.push({
        label: "Copy",
        action: (e, cell) => {
          const value = cell.getValue();
          navigator.clipboard.writeText(value);
        },
      });
    }

    if (allowPaste) {
      operations.push({
        label: "Paste",
        action: (e, cell) => {
          if (cell.getElement().classList.contains("disable-editing")) {
            return;
          }
          navigator.clipboard.readText().then((text) => {
            try {
              const columnDef = cell.getColumn().getDefinition();
              const rowData = cell.getRow().getData();
              const validatedValue = tabulatorInstance.validateCellValue(
                text,
                columnDef,
                rowData
              );
              cell.setValue(validatedValue);
            } catch (error) {
              showNotification(error.message, "error");
            }
          });
        },
      });
    }
  }

  return operations.length ? operations : [];
}
