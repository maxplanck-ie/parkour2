export const REQUEST_FILE_TYPE_OTHER = "Other";

export const REQUEST_FILE_TYPE_OPTIONS = [REQUEST_FILE_TYPE_OTHER];

const REQUEST_FILE_TYPE_PATTERN = /^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$/;
const REQUEST_FILE_TYPE_MAX_LENGTH = 100;

export function isValidRequestFileType(value) {
  const text = String(value || "");
  return (
    text.length <= REQUEST_FILE_TYPE_MAX_LENGTH &&
    REQUEST_FILE_TYPE_PATTERN.test(text)
  );
}

export function areRequestFileTypesSelected(files = []) {
  return (
    files.length > 0 &&
    files.every((file) => {
      if (!file.fileTypeChoice) return false;
      if (file.fileTypeChoice !== REQUEST_FILE_TYPE_OTHER) return true;
      return (
        !file.customFileType || isValidRequestFileType(file.customFileType)
      );
    })
  );
}

export function requestFileTypeOptionsFromResponse(data = []) {
  const names = Array.isArray(data)
    ? data.map((item) => String(item?.name || "").trim())
    : [];
  return [
    ...new Set(
      names.filter(
        (name) =>
          name !== REQUEST_FILE_TYPE_OTHER && isValidRequestFileType(name),
      ),
    ),
    REQUEST_FILE_TYPE_OTHER,
  ];
}

export function normaliseRequestFile(
  file = {},
  options = REQUEST_FILE_TYPE_OPTIONS,
) {
  const storedType = String(file.file_type || REQUEST_FILE_TYPE_OTHER);
  const isKnownType = options.includes(storedType);
  return {
    ...file,
    file_type: storedType,
    fileTypeChoice: isKnownType ? storedType : REQUEST_FILE_TYPE_OTHER,
    customFileType: isKnownType ? "" : storedType,
  };
}

export function resolveRequestFileType(file = {}) {
  if (file.fileTypeChoice !== REQUEST_FILE_TYPE_OTHER) {
    return file.fileTypeChoice;
  }
  return String(file.customFileType || REQUEST_FILE_TYPE_OTHER).trim();
}

export function requestFileTypesPayload(files = []) {
  return Object.fromEntries(
    files
      .filter((file) => file?.id !== undefined && file?.id !== null)
      .map((file) => [String(file.id), resolveRequestFileType(file)]),
  );
}
