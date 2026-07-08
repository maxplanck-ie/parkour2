<template>
  <div
    v-if="activeAction === requestActions.uploadSigned"
    class="popup-overlay"
    :class="{ 'drag-over': isUploadDragOver }"
    tabindex="0"
    @keydown="handlePopupKeydown"
    @dragover.prevent="handleUploadDragOver"
    @dragenter.prevent="handleUploadDragEnter"
    @dragleave.prevent="handleUploadDragLeave"
    @drop.prevent="handleUploadDrop"
  >
    <div
      class="popup-container request-action-modal"
      :style="{ width: '520px' }"
    >
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_upload_signed_request.svg"
            alt=""
          />
          <span>Upload file</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body">
        <div class="upload-row">
          <label class="upload-label">File:</label>
          <input
            class="upload-input"
            type="text"
            :value="uploadFileName"
            readonly
            placeholder="Select a file"
          />
          <button
            class="popup-button secondary"
            type="button"
            @click="triggerUploadInput"
          >
            Select
          </button>
          <input
            ref="uploadInput"
            type="file"
            class="hidden-input"
            @change="handleUploadSelection"
          />
        </div>
        <div class="upload-drop-zone" :class="{ active: isUploadDragOver }">
          <div class="drop-title">Drag &amp; drop the signed request here</div>
          <div class="drop-subtitle">Accepted formats: PDF, DOCX</div>
        </div>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultUploadButton"
          class="popup-button yes-button"
          type="button"
          :disabled="uploadBusy"
          @click="submitSignedRequest"
        >
          <span v-if="uploadBusy">Uploading...</span>
          <span v-else>Upload</span>
        </button>
        <button class="popup-button secondary" type="button" @click="close">
          Cancel
        </button>
      </div>
    </div>
  </div>

  <div
    v-if="activeAction === requestActions.filePaths"
    class="popup-overlay"
    tabindex="0"
    @keydown="handlePopupKeydown"
  >
    <div class="popup-container request-action-modal filepaths-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_view_file_paths.svg"
            alt=""
          />
          <span>File Paths</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body filepaths-body">
        <div class="filepaths-request-name">
          <span class="label">Request Name:</span>
          <span class="value">{{ requestContext?.name || "-" }}</span>
        </div>
        <div class="filepaths-columns">
          <div class="filepaths-column filepaths-left">
            <div class="filepaths-header">
              <span>Request File Paths:</span>
              <div
                class="filepaths-os-select"
                title="Change OS to format file paths"
              >
                <font-awesome-icon
                  class="filepaths-os-icon"
                  icon="fa-solid fa-desktop"
                />
                <select v-model="selectedOS" class="filepaths-select">
                  <option :value="filepathOs.linux">Linux</option>
                  <option :value="filepathOs.macOS">macOS</option>
                  <option :value="filepathOs.windows">Windows</option>
                </select>
              </div>
            </div>
            <div class="filepaths-list filepaths-list-box">
              <div class="filepaths-scroll">
                <div
                  v-for="entry in formattedFilepaths"
                  :key="entry.key"
                  class="filepaths-row"
                >
                  <div class="filepaths-key">{{ entry.key }}</div>
                  <button
                    class="filepaths-value filepaths-input"
                    type="button"
                    @click="copyText(entry.copyValue)"
                  >
                    <span>{{ entry.value || "Empty" }}</span>
                    <span v-if="entry.md5" class="filepaths-md5">
                      MD5: {{ entry.md5 }}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="filepaths-column filepaths-right">
            <div class="filepaths-header">
              <span>Request User Paths:</span>
              <button
                class="popup-button secondary small"
                type="button"
                @click="startAddUserPath"
                title="Add User Path"
              >
                <font-awesome-icon icon="fa-solid fa-square-plus" />
                <span>Add</span>
              </button>
            </div>
            <div class="filepaths-list filepaths-list-box">
              <div class="userpaths-scroll">
                <div v-if="showUserPathForm" class="userpath-form">
                  <input
                    v-model.trim="userPathForm.name"
                    type="text"
                    placeholder="Name"
                  />
                  <input
                    v-model.trim="userPathForm.value"
                    type="text"
                    placeholder="Path"
                  />
                  <input
                    v-model.trim="userPathForm.md5"
                    type="text"
                    placeholder="MD5 (optional)"
                  />
                  <div class="userpath-actions">
                    <button
                      class="popup-button yes-button small"
                      type="button"
                      :disabled="!canSaveUserPath"
                      @click="saveUserPath"
                    >
                      Save
                    </button>
                    <button
                      class="popup-button small"
                      type="button"
                      @click="cancelUserPath"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
                <div v-if="!hasUserPaths" class="empty-state">
                  No User Paths
                </div>
                <div
                  v-for="path in displayUserPaths"
                  :key="path.id"
                  class="filepaths-row userpath-row"
                >
                  <div class="filepaths-key">{{ path.name }}</div>
                  <button
                    class="filepaths-value filepaths-input userpath-value"
                    type="button"
                    @click="copyText(path.copyValue || 'Empty')"
                  >
                    <span>{{ path.value || "Empty" }}</span>
                    <span v-if="path.md5" class="filepaths-md5">
                      MD5: {{ path.md5 }}
                    </span>
                  </button>
                  <div class="userpath-icons">
                    <button
                      class="icon-button"
                      type="button"
                      title="Edit"
                      @click="startEditUserPath(path)"
                    >
                      <font-awesome-icon icon="fa-solid fa-pen" />
                    </button>
                    <button
                      class="icon-button danger"
                      type="button"
                      title="Delete"
                      @click="confirmDeleteUserPath(path)"
                    >
                      <font-awesome-icon icon="fa-solid fa-trash" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultFilepathsButton"
          class="popup-button yes-button"
          type="button"
          @click="close"
        >
          Close
        </button>
      </div>
    </div>
  </div>

  <div
    v-if="activeAction === requestActions.composeEmail"
    class="popup-overlay"
    tabindex="0"
    @keydown="handlePopupKeydown"
  >
    <div class="popup-container request-action-modal email-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_compose_email.svg"
            alt=""
          />
          <span>New Email</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body email-body">
        <label class="email-field">
          <span>Subject:</span>
          <input
            v-model="emailForm.subject"
            type="text"
            placeholder="Subject"
            :class="{ 'input-error': emailErrors.subject }"
            @input="clearEmailFieldError('subject')"
          />
          <div v-if="emailErrors.subject" class="field-error">
            {{ emailErrors.subject }}
          </div>
        </label>
        <label class="email-field">
          <span>Message:</span>
          <textarea
            v-model="emailForm.message"
            rows="6"
            placeholder="Message"
            :class="{ 'input-error': emailErrors.message }"
            @input="clearEmailFieldError('message')"
          ></textarea>
          <div v-if="emailErrors.message" class="field-error">
            {{ emailErrors.message }}
          </div>
        </label>
        <label class="email-checkbox">
          <input type="checkbox" v-model="emailForm.includeFailed" />
          <span>Include the list of all failed libraries and samples</span>
        </label>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultComposeButton"
          class="popup-button yes-button with-icon"
          type="button"
          :disabled="emailBusy"
          @click="sendEmail"
        >
          <font-awesome-icon icon="fa-solid fa-paper-plane" />
          <span>{{ emailBusy ? "Sending..." : "Send" }}</span>
        </button>
      </div>
    </div>
  </div>

  <div
    v-if="activeAction === requestActions.solicitApproval"
    class="popup-overlay"
    tabindex="0"
    @keydown="handlePopupKeydown"
  >
    <div class="popup-container request-action-modal approval-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_solicit_approval.svg"
            alt=""
          />
          <span>New Email for Approval Solicitation</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body email-body">
        <label class="email-field">
          <span>Subject:</span>
          <input
            v-model="approvalForm.subject"
            type="text"
            placeholder="Subject"
            :class="{ 'input-error': approvalErrors.subject }"
            @input="clearApprovalFieldError('subject')"
          />
          <div v-if="approvalErrors.subject" class="field-error">
            {{ approvalErrors.subject }}
          </div>
        </label>
        <label class="email-field">
          <span>Message:</span>
          <textarea
            v-model="approvalForm.message"
            rows="6"
            placeholder="Message"
            :class="{ 'input-error': approvalErrors.message }"
            @input="clearApprovalFieldError('message')"
          ></textarea>
          <div v-if="approvalErrors.message" class="field-error">
            {{ approvalErrors.message }}
          </div>
        </label>
        <label class="email-checkbox">
          <input type="checkbox" v-model="approvalForm.includeRecords" />
          <span>Include the list of all libraries and samples</span>
        </label>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultApprovalButton"
          class="popup-button yes-button with-icon"
          type="button"
          :disabled="approvalBusy"
          @click="sendApprovalEmail"
        >
          <font-awesome-icon icon="fa-solid fa-paper-plane" />
          <span>{{ approvalBusy ? "Sending..." : "Send" }}</span>
        </button>
      </div>
    </div>
  </div>

  <div
    v-if="activeAction === requestActions.deleteRequest"
    class="popup-overlay"
    tabindex="0"
    @keydown="handlePopupKeydown"
  >
    <div
      class="popup-container request-action-modal"
      :style="{ width: '420px' }"
    >
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_delete_request.svg"
            alt=""
          />
          <span>Delete Request</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body">
        <div class="confirm-message">
          Are you sure that you want to delete the request "{{
            requestContext?.name
          }}"?
        </div>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultDeleteButton"
          class="popup-button yes-button"
          type="button"
          :disabled="deleteBusy"
          @click="confirmDelete"
        >
          <span v-if="deleteBusy">Deleting...</span>
          <span v-else>Delete</span>
        </button>
        <button class="popup-button secondary" type="button" @click="close">
          Cancel
        </button>
      </div>
    </div>
  </div>

  <div
    v-if="activeAction === requestActions.attachments"
    class="popup-overlay"
    :class="{ 'drag-over': isAttachmentsDragOver }"
    tabindex="0"
    @keydown="handlePopupKeydown"
    @dragover.prevent="handleAttachmentsDragOver"
    @dragenter.prevent="handleAttachmentsDragEnter"
    @dragleave.prevent="handleAttachmentsDragLeave"
    @drop.prevent="handleAttachmentsDrop"
  >
    <div v-if="canEditAttachments" class="drag-drop-indicator">
      <div
        style="
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
        "
      >
        <p>
          Drop <span style="font-weight: bold">request related documents</span>
          here to upload
        </p>
      </div>
    </div>
    <div class="popup-container request-action-modal attachments-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img
            class="popup-title-icon"
            src="@/assets/icons/action_attachments.svg"
            alt=""
          />
          <span>Attachments</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">
          &times;
        </button>
      </div>
      <div class="popup-body attachments-body">
        <div class="files-section">
          <div class="files-header">
            <div>
              <span>Files</span>
              <small>Upload request related documents.</small>
            </div>
            <button
              v-if="canEditAttachments"
              class="header-button ghost"
              type="button"
              :disabled="attachmentsBusy"
              @click="triggerAttachmentsUpload"
            >
              <font-awesome-icon
                icon="fa-solid fa-square-plus"
                style="color: white"
              />
              <span>Add Files</span>
            </button>
            <input
              ref="attachmentsFileInput"
              type="file"
              multiple
              @change="handleAttachmentsSelection"
              style="display: none"
            />
          </div>
          <div class="files-table-wrapper">
            <table
              class="files-table"
              :class="{ 'files-table-empty': !attachmentsFiles.length }"
            >
              <thead>
                <tr>
                  <th style="width: 60%">Name</th>
                  <th style="width: 14%">Size</th>
                  <th style="width: 26%"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!attachmentsFiles.length">
                  <td colspan="3" class="empty-cell">No files uploaded yet.</td>
                </tr>
                <tr v-for="file in attachmentsFiles" :key="file.id">
                  <td class="file-name-cell">
                    <span class="file-name-text" :title="file.name">{{
                      file.name
                    }}</span>
                  </td>
                  <td class="file-size-cell" :title="formatFileSize(file.size)">
                    {{ formatFileSize(file.size) }}
                  </td>
                  <td class="actions-cell">
                    <button
                      type="button"
                      class="icon-action"
                      :title="
                        file.path
                          ? `Download ${file.name}`
                          : 'Download unavailable'
                      "
                      :disabled="!file.path"
                      @click="downloadAttachment(file)"
                    >
                      <font-awesome-icon icon="fa-solid fa-download" />
                    </button>
                    <button
                      v-if="canEditAttachments"
                      type="button"
                      class="icon-action danger"
                      :title="`Remove ${file.name}`"
                      :disabled="attachmentsBusy"
                      @click="removeAttachment(file)"
                    >
                      <font-awesome-icon icon="fa-solid fa-xmark" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="popup-footer">
        <button
          ref="defaultAttachmentsButton"
          class="popup-button yes-button"
          type="button"
          :disabled="attachmentsBusy"
          @click="close"
        >
          Close
        </button>
      </div>
    </div>
  </div>

</template>

<script>
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

const REQUEST_ACTIONS = {
  uploadSigned: "uploadSigned",
  filePaths: "filePaths",
  composeEmail: "composeEmail",
  solicitApproval: "solicitApproval",
  deleteRequest: "deleteRequest",
  attachments: "attachments"
};

const REQUEST_ACTION_DEFAULT_REFS = {
  [REQUEST_ACTIONS.uploadSigned]: "defaultUploadButton",
  [REQUEST_ACTIONS.filePaths]: "defaultFilepathsButton",
  [REQUEST_ACTIONS.deleteRequest]: "defaultDeleteButton",
  [REQUEST_ACTIONS.attachments]: "defaultAttachmentsButton"
};

const REQUEST_API_ENDPOINTS = {
  request: (requestId) => `/api/requests/${requestId}/`,
  requestRecords: (requestId) => `/api/requests/${requestId}/get_records/`,
  requestEdit: (requestId) => `/api/requests/${requestId}/edit/`,
  uploadSignedRequest: (requestId) =>
    `/api/requests/${requestId}/upload_deep_sequencing_request/`,
  putMetapaths: (requestId) => `/api/requests/${requestId}/put_metapaths/`,
  sendEmail: (requestId) => `/api/requests/${requestId}/send_email/`,
  solicitApproval: (requestId) =>
    `/api/requests/${requestId}/solicit_approval/`,
  uploadFiles: "/api/requests/upload_files/",
  filesAfterUpload: "/api/requests/get_files_after_upload/"
};

const apiUrl = (endpoint) => `${urlStringStart}${endpoint}`;

const FILEPATH_OS = {
  linux: "Linux",
  macOS: "macOS",
  windows: "Windows"
};

const USER_PATH_MODES = {
  add: "add",
  edit: "edit"
};

const MULTIPART_FORM_HEADERS = {
  headers: { "Content-Type": "multipart/form-data" }
};

const RESPONSE_TYPES = {
  blob: "blob"
};

const NOTIFICATION_TYPES = {
  success: "success",
  warning: "warning",
  error: "error"
};

const FORM_FIELDS = {
  file: "file",
  files: "files",
  data: "data",
  subject: "subject",
  message: "message",
  includeFailedRecords: "include_failed_records",
  includeRecords: "include_records"
};

const REQUEST_DATA_FIELDS = {
  filepathsData: "data",
  filepathsMetadata: "metadata",
  costUnit: "cost_unit",
  description: "description",
  recordType: "record_type"
};

export default {
  name: "RequestActionsPopups",
  emits: ["close", "refresh"],
  props: {
    activeAction: {
      type: String,
      default: null
    },
    requestContext: {
      type: Object,
      default: null
    },
    isStaffUser: {
      type: Boolean,
      default: false
    },
    paperlessApproval: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      requestActions: REQUEST_ACTIONS,
      filepathOs: FILEPATH_OS,
      uploadFile: null,
      isUploadDragOver: false,
      uploadBusy: false,
      filepaths: {},
      userPaths: [],
      selectedOS: FILEPATH_OS.linux,
      showUserPathForm: false,
      userPathForm: {
        mode: USER_PATH_MODES.add,
        id: null,
        name: "",
        value: "",
        md5: ""
      },
      emailForm: {
        subject: "",
        message: "",
        includeFailed: false
      },
      emailErrors: {
        subject: "",
        message: ""
      },
      approvalForm: {
        subject: "",
        message: "",
        includeRecords: true
      },
      approvalErrors: {
        subject: "",
        message: ""
      },
      emailBusy: false,
      approvalBusy: false,
      deleteBusy: false,
      attachmentsFiles: [],
      attachmentsFileIds: [],
      attachmentsBusy: false,
      isAttachmentsDragOver: false,
      attachmentsRequestDetails: {
        [REQUEST_DATA_FIELDS.costUnit]: null,
        [REQUEST_DATA_FIELDS.description]: ""
      },
      attachmentsRecords: []
    };
  },
  computed: {
    uploadFileName() {
      return this.uploadFile ? this.uploadFile.name : "";
    },
    formattedFilepaths() {
      const entries = [];
      const filepaths = this.filepaths || {};
      Object.keys(filepaths).forEach((key) => {
        const rawValue = filepaths[key];
        const pathValue = this.pathReferencePath(rawValue);
        const formatted =
          key === REQUEST_DATA_FIELDS.filepathsData ||
          key === REQUEST_DATA_FIELDS.filepathsMetadata
            ? this.formatPathForOS(pathValue)
            : pathValue || "";
        const md5 = this.pathReferenceMd5(rawValue);
        entries.push({
          key,
          value: formatted,
          md5,
          copyValue: this.pathReferenceCopyValue(formatted, md5)
        });
      });
      return entries;
    },
    hasUserPaths() {
      return this.userPaths.some(
        (item) => item.value !== null && item.value !== ""
      );
    },
    displayUserPaths() {
      return this.hasUserPaths
        ? this.userPaths.map((path) => {
            const md5 = this.pathReferenceMd5(path.rawValue ?? path.value);
            return {
              ...path,
              md5,
              copyValue: this.pathReferenceCopyValue(path.value, md5)
            };
          })
        : [];
    },
    canSaveUserPath() {
      return Boolean(this.userPathForm.name && this.userPathForm.value);
    },
    canEditAttachments() {
      const canEdit = this.requestContext?.canEditRequest;
      return canEdit === undefined ? true : Boolean(canEdit);
    }
  },
  mounted() {
    document.addEventListener("keydown", this.handleGlobalKeydown);
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this.handleGlobalKeydown);
  },
  watch: {
    activeAction(newVal) {
      if (!newVal) return;
      this.resetStateForAction(newVal);
      if (newVal === REQUEST_ACTIONS.filePaths) {
        this.fetchFilepaths();
      }
      if (newVal === REQUEST_ACTIONS.composeEmail) {
        this.emailForm.subject = this.requestContext?.name || "";
        this.emailForm.message = "";
        this.emailForm.includeFailed = false;
        this.clearEmailErrors();
      }
      if (newVal === REQUEST_ACTIONS.solicitApproval) {
        this.approvalForm.subject = this.requestContext?.name || "";
        this.approvalForm.message = "";
        this.approvalForm.includeRecords = true;
        this.clearApprovalErrors();
      }
      if (newVal === REQUEST_ACTIONS.attachments) {
        this.loadAttachments();
      }

      this.$nextTick(() => {
        const refName = REQUEST_ACTION_DEFAULT_REFS[newVal];
        if (refName && this.$refs[refName]?.focus) {
          this.$refs[refName].focus();
        }
      });
    },
    requestContext() {
      if (this.activeAction === REQUEST_ACTIONS.composeEmail) {
        this.emailForm.subject = this.requestContext?.name || "";
        this.clearEmailFieldError("subject");
      }
      if (this.activeAction === REQUEST_ACTIONS.solicitApproval) {
        this.approvalForm.subject = this.requestContext?.name || "";
        this.clearApprovalFieldError("subject");
      }
      if (this.activeAction === REQUEST_ACTIONS.attachments) {
        this.loadAttachments();
      }
    }
  },
  methods: {
    handleGlobalKeydown(event) {
      if (!this.activeAction) return;
      if (event.key !== "Escape") return;
      event.preventDefault();
      this.close();
    },
    handlePopupKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        this.close();
        return;
      }
      if (event.key === "Enter") {
        if (
          this.activeAction === REQUEST_ACTIONS.composeEmail ||
          this.activeAction === REQUEST_ACTIONS.solicitApproval
        ) {
          return;
        }
        event.preventDefault();
        if (this.activeAction === REQUEST_ACTIONS.uploadSigned) {
          if (!this.uploadBusy) this.submitSignedRequest();
          return;
        }
        if (this.activeAction === REQUEST_ACTIONS.deleteRequest) {
          if (!this.deleteBusy) this.confirmDelete();
          return;
        }
        if (this.activeAction === REQUEST_ACTIONS.filePaths) {
          this.close();
        }
      }
    },
    close() {
      this.$emit("close");
    },
    resetStateForAction(action) {
      this.uploadFile = null;
      this.isUploadDragOver = false;
      this.uploadBusy = false;
      this.filepaths = {};
      this.userPaths = [];
      this.showUserPathForm = false;
      this.userPathForm = {
        mode: USER_PATH_MODES.add,
        id: null,
        name: "",
        value: "",
        md5: ""
      };
      this.emailBusy = false;
      this.approvalBusy = false;
      this.deleteBusy = false;
      this.attachmentsFiles = [];
      this.attachmentsFileIds = [];
      this.attachmentsBusy = false;
      this.isAttachmentsDragOver = false;
      this.attachmentsRequestDetails = {
        [REQUEST_DATA_FIELDS.costUnit]: null,
        [REQUEST_DATA_FIELDS.description]: ""
      };
      this.attachmentsRecords = [];
      if (action === REQUEST_ACTIONS.filePaths) {
        this.selectedOS = this.detectOS(navigator.userAgent);
      }
    },
    triggerUploadInput() {
      this.$refs.uploadInput?.click?.();
    },
    handleUploadSelection(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      this.uploadFile = file;
    },
    handleUploadDragOver() {
      this.isUploadDragOver = true;
    },
    handleUploadDragEnter() {
      this.isUploadDragOver = true;
    },
    handleUploadDragLeave(event) {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        this.isUploadDragOver = false;
      }
    },
    handleUploadDrop(event) {
      this.isUploadDragOver = false;
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        this.uploadFile = file;
      }
    },
    async submitSignedRequest() {
      if (!this.requestContext?.id) return;
      if (!this.uploadFile) {
        showNotification("No file selected.", NOTIFICATION_TYPES.warning);
        return;
      }
      const formData = new FormData();
      formData.append(FORM_FIELDS.file, this.uploadFile);
      try {
        this.uploadBusy = true;
        const response = await axiosRef.post(
          apiUrl(
            REQUEST_API_ENDPOINTS.uploadSignedRequest(this.requestContext.id)
          ),
          formData,
          MULTIPART_FORM_HEADERS
        );
        if (response?.data?.success) {
          showNotification(
            "Signed request uploaded successfully.",
            NOTIFICATION_TYPES.success
          );
          this.$emit("refresh");
          this.close();
        } else {
          showNotification(
            "Signed request upload failed.",
            NOTIFICATION_TYPES.error
          );
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.uploadBusy = false;
      }
    },
    async fetchFilepaths() {
      if (!this.requestContext?.id) return;
      try {
        const response = await axiosRef.get(
          apiUrl(REQUEST_API_ENDPOINTS.request(this.requestContext.id))
        );
        const data = response?.data || {};
        this.filepaths = data.filepaths || {};
        const metapaths = data.metapaths || {};
        this.userPaths = Object.entries(metapaths).map(
          ([name, value], index) => ({
            id: index + 1,
            name,
            value: this.pathReferencePath(value),
            rawValue: value
          })
        );
      } catch (error) {
        handleError(error);
      }
    },
    pathReferencePath(value) {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        return value.path || "";
      }
      return value || "";
    },
    pathReferenceMd5(value) {
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        return "";
      }
      return value.md5 || "";
    },
    pathReferenceCopyValue(path, md5) {
      const cleanPath = path || "Empty";
      return md5 ? `${cleanPath}\nMD5: ${md5}` : cleanPath;
    },
    buildPathReferenceValue(path, md5) {
      if (!md5) return path;
      return {
        path,
        md5
      };
    },
    formatPathForOS(filepath) {
      const filepathRegex =
        /^\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_/.]+$/;
      if (!filepath) {
        return "Empty";
      }
      if (filepathRegex.test(filepath)) {
        const filepathSplit = filepath.split("/").filter((item) => item !== "");
        if (this.selectedOS === FILEPATH_OS.windows) {
          return `\\\\${filepathSplit[0]}\\${filepathSplit[1]}-${filepathSplit[2]}\\${filepathSplit
            .slice(3)
            .join("\\")}`;
        }
        if (this.selectedOS === FILEPATH_OS.macOS) {
          return `smb://${filepathSplit[0]}/${filepathSplit[1]}-${filepathSplit[2]}/${filepathSplit
            .slice(3)
            .join("/")}`;
        }
        return filepath;
      }
      return filepath;
    },
    detectOS(userAgent) {
      if (/Mac OS X/.test(userAgent)) {
        return FILEPATH_OS.macOS;
      }
      if (/Windows NT/.test(userAgent)) {
        return FILEPATH_OS.windows;
      }
      return FILEPATH_OS.linux;
    },
    async copyText(text) {
      try {
        await navigator.clipboard.writeText(text || "");
        showNotification(
          "Path copied to clipboard.",
          NOTIFICATION_TYPES.success
        );
      } catch {
        showNotification("Path copy failed.", NOTIFICATION_TYPES.error);
      }
    },
    startAddUserPath() {
      this.showUserPathForm = true;
      this.userPathForm = {
        mode: USER_PATH_MODES.add,
        id: null,
        name: "",
        value: "",
        md5: ""
      };
    },
    startEditUserPath(path) {
      this.showUserPathForm = true;
      this.userPathForm = {
        mode: USER_PATH_MODES.edit,
        id: path.id,
        name: path.name,
        value: path.value,
        md5: path.md5 || this.pathReferenceMd5(path.rawValue) || ""
      };
    },
    cancelUserPath() {
      this.showUserPathForm = false;
      this.userPathForm = {
        mode: USER_PATH_MODES.add,
        id: null,
        name: "",
        value: "",
        md5: ""
      };
    },
    async saveUserPath() {
      if (!this.canSaveUserPath) return;
      const newName = this.userPathForm.name;
      const newValue = this.userPathForm.value;
      const newMd5 = this.userPathForm.md5;
      const current = this.userPaths.slice();
      const map = new Map();

      if (this.userPathForm.mode === USER_PATH_MODES.add) {
        if (current.some((item) => item.name === newName)) {
          showNotification(
            "User path name already exists.",
            NOTIFICATION_TYPES.warning
          );
          return;
        }
        map.set(newName, this.buildPathReferenceValue(newValue, newMd5));
        current.forEach((item) => {
          if (item.value !== null) map.set(item.name, item.rawValue ?? item.value);
        });
      } else {
        current.forEach((item) => {
          if (item.id === this.userPathForm.id) {
            map.set(
              newName,
              this.buildPathReferenceValue(newValue, newMd5, item.rawValue)
            );
          } else {
            map.set(item.name, item.rawValue ?? item.value);
          }
        });
      }

      await this.persistUserPaths(Object.fromEntries(map));
    },
    confirmDeleteUserPath(path) {
      if (!path?.name) return;
      const confirmed = window.confirm(
        `Are you sure that you want to delete path '${path.name}'?`
      );
      if (!confirmed) return;
      const updated = {};
      this.userPaths.forEach((item) => {
        if (item.name !== path.name) {
          updated[item.name] = item.value;
        }
      });
      this.persistUserPaths(updated);
    },
    async persistUserPaths(userpaths) {
      if (!this.requestContext?.id) return;
      try {
        const response = await axiosRef.post(
          apiUrl(REQUEST_API_ENDPOINTS.putMetapaths(this.requestContext.id)),
          userpaths
        );
        if (response?.data?.success) {
          showNotification(
            "User path saved successfully.",
            NOTIFICATION_TYPES.success
          );
          this.userPaths = Object.entries(userpaths).map(
            ([name, value], index) => ({
              id: index + 1,
              name,
              value: this.pathReferencePath(value),
              rawValue: value
            })
          );
          this.showUserPathForm = false;
        } else {
          showNotification("User path save failed.", NOTIFICATION_TYPES.error);
        }
      } catch (error) {
        handleError(error);
      }
    },
    async sendEmail() {
      if (!this.requestContext?.id) return;
      if (!this.validateEmailForm()) {
        showNotification(
          "All fields are required.",
          NOTIFICATION_TYPES.warning
        );
        return;
      }
      const formData = new FormData();
      formData.append(FORM_FIELDS.subject, this.emailForm.subject);
      formData.append(FORM_FIELDS.message, this.emailForm.message);
      formData.append(
        FORM_FIELDS.includeFailedRecords,
        String(this.emailForm.includeFailed)
      );
      try {
        this.emailBusy = true;
        await axiosRef.post(
          apiUrl(REQUEST_API_ENDPOINTS.sendEmail(this.requestContext.id)),
          formData,
          MULTIPART_FORM_HEADERS
        );
        showNotification("Email sent successfully.", NOTIFICATION_TYPES.success);
        this.close();
      } catch (error) {
        handleError(error);
      } finally {
        this.emailBusy = false;
      }
    },
    clearEmailErrors() {
      this.emailErrors = this.emptyEmailFieldErrors();
    },
    clearEmailFieldError(field) {
      this.clearEmailFormFieldError("emailErrors", field);
    },
    validateEmailForm() {
      return this.validateRequiredEmailFields(this.emailForm, "emailErrors");
    },
    async sendApprovalEmail() {
      if (!this.requestContext?.id) return;
      if (!this.validateApprovalForm()) {
        showNotification(
          "All fields are required.",
          NOTIFICATION_TYPES.warning
        );
        return;
      }
      const formData = new FormData();
      formData.append(FORM_FIELDS.subject, this.approvalForm.subject);
      formData.append(FORM_FIELDS.message, this.approvalForm.message);
      formData.append(
        FORM_FIELDS.includeRecords,
        String(this.approvalForm.includeRecords)
      );
      try {
        this.approvalBusy = true;
        const response = await axiosRef.post(
          apiUrl(REQUEST_API_ENDPOINTS.solicitApproval(this.requestContext.id)),
          formData,
          MULTIPART_FORM_HEADERS
        );
        if (response?.data?.success) {
          showNotification(
            "Approval email sent to PI.",
            NOTIFICATION_TYPES.success
          );
          this.close();
        } else {
          showNotification(
            "Approval email failed.",
            NOTIFICATION_TYPES.error
          );
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.approvalBusy = false;
      }
    },
    clearApprovalErrors() {
      this.approvalErrors = this.emptyEmailFieldErrors();
    },
    clearApprovalFieldError(field) {
      this.clearEmailFormFieldError("approvalErrors", field);
    },
    validateApprovalForm() {
      return this.validateRequiredEmailFields(
        this.approvalForm,
        "approvalErrors"
      );
    },
    emptyEmailFieldErrors() {
      return {
        subject: "",
        message: ""
      };
    },
    clearEmailFormFieldError(errorStateKey, field) {
      if (!this[errorStateKey]?.[field]) return;
      this[errorStateKey] = {
        ...this[errorStateKey],
        [field]: ""
      };
    },
    validateRequiredEmailFields(form, errorStateKey) {
      const errors = {
        subject: "",
        message: ""
      };
      if (!String(form.subject || "").trim()) {
        errors.subject = "Subject is a required field.";
      }
      if (!String(form.message || "").trim()) {
        errors.message = "Message is a required field.";
      }
      this[errorStateKey] = errors;
      return !errors.subject && !errors.message;
    },
    async confirmDelete() {
      if (!this.requestContext?.id) return;
      try {
        this.deleteBusy = true;
        const response = await axiosRef.delete(
          apiUrl(REQUEST_API_ENDPOINTS.request(this.requestContext.id))
        );
        if (response?.status === 204 || response?.data?.success) {
          showNotification(
            "Request deleted successfully.",
            NOTIFICATION_TYPES.success
          );
          this.$emit("refresh");
          this.close();
        } else {
          showNotification(
            "Request deletion failed.",
            NOTIFICATION_TYPES.error
          );
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.deleteBusy = false;
      }
    },
    formatFileSize(size) {
      if (size === undefined || size === null) return "-";
      if (typeof size === "string") {
        const trimmed = size.trim();
        if (!trimmed.length) return "-";
        const numericValue = Number(trimmed);
        if (Number.isNaN(numericValue)) return trimmed;
        size = numericValue;
      }
      const value = Number(size);
      if (Number.isNaN(value)) return "-";
      if (value >= 1024 * 1024) {
        return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      }
      if (value >= 1024) {
        return `${(value / 1024).toFixed(1)} KB`;
      }
      return `${value} B`;
    },
    async loadAttachments({ force = false } = {}) {
      if (!this.requestContext?.id) return;
      const meta = force ? null : this.requestContext?.meta || null;
      const records = Array.isArray(this.requestContext?.records)
        ? this.requestContext.records
        : [];

      if (meta) {
        const filesList = Array.isArray(meta?.files) ? meta.files : [];
        this.attachmentsFiles = filesList.map((file) => ({
          id: file?.id ?? file?.pk,
          name: file?.name,
          size: file?.size ?? null,
          path: file?.path
        }));
        this.attachmentsFileIds = this.attachmentsFiles
          .map((file) => file?.id)
          .filter((id) => id !== undefined && id !== null);

          this.attachmentsRequestDetails = {
            [REQUEST_DATA_FIELDS.costUnit]:
              meta?.[REQUEST_DATA_FIELDS.costUnit] ?? null,
            [REQUEST_DATA_FIELDS.description]:
              meta?.[REQUEST_DATA_FIELDS.description] ?? ""
          };
      }

      if (records.length) {
        this.attachmentsRecords = records
          .filter(
            (record) => record?.pk && record?.[REQUEST_DATA_FIELDS.recordType]
          )
          .map((record) => ({
            pk: record.pk,
            [REQUEST_DATA_FIELDS.recordType]:
              record[REQUEST_DATA_FIELDS.recordType]
          }));
      }

      const needsRequest =
        force ||
        !meta ||
        this.attachmentsRequestDetails[REQUEST_DATA_FIELDS.costUnit] ===
          null ||
        this.attachmentsRequestDetails[REQUEST_DATA_FIELDS.description] === "";
      const needsRecords = force
        ? !records.length
        : !this.attachmentsRecords.length;

      if (!needsRequest && !needsRecords) {
        return;
      }

      this.attachmentsBusy = true;
      try {
        const requestId = this.requestContext.id;
        const [requestRes, recordsRes] = await Promise.allSettled([
          needsRequest
            ? axiosRef.get(apiUrl(REQUEST_API_ENDPOINTS.request(requestId)))
            : Promise.resolve({ data: meta }),
          needsRecords
            ? axiosRef.get(
                apiUrl(REQUEST_API_ENDPOINTS.requestRecords(requestId))
              )
            : Promise.resolve({ data: records })
        ]);

        const requestData =
          requestRes.status === "fulfilled" ? requestRes.value?.data || {} : {};
        if (needsRequest) {
          const filesList = Array.isArray(requestData?.files)
            ? requestData.files
            : [];
          this.attachmentsFiles = filesList.map((file) => ({
            id: file?.id ?? file?.pk,
            name: file?.name,
            size: file?.size ?? null,
            path: file?.path
          }));
          this.attachmentsFileIds = this.attachmentsFiles
            .map((file) => file?.id)
            .filter((id) => id !== undefined && id !== null);
          this.attachmentsRequestDetails = {
            [REQUEST_DATA_FIELDS.costUnit]:
              requestData?.[REQUEST_DATA_FIELDS.costUnit] ?? null,
            [REQUEST_DATA_FIELDS.description]:
              requestData?.[REQUEST_DATA_FIELDS.description] ?? ""
          };
        }

        if (needsRecords) {
          const recordsData =
            recordsRes.status === "fulfilled"
              ? recordsRes.value?.data || []
              : [];
          this.attachmentsRecords = Array.isArray(recordsData)
            ? recordsData
                .filter(
                  (record) =>
                    record?.pk && record?.[REQUEST_DATA_FIELDS.recordType]
                )
                .map((record) => ({
                  pk: record.pk,
                  [REQUEST_DATA_FIELDS.recordType]:
                    record[REQUEST_DATA_FIELDS.recordType]
                }))
            : [];
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.attachmentsBusy = false;
      }
    },
    triggerAttachmentsUpload() {
      this.$refs.attachmentsFileInput?.click?.();
    },
    async handleAttachmentsSelection(event) {
      const files = Array.from(event.target.files || []);
      try {
        await this.uploadAttachments(files);
      } catch (error) {
        handleError(error);
      } finally {
        if (event?.target) {
          event.target.value = "";
        }
      }
    },
    handleAttachmentsDragOver() {
      if (!this.canEditAttachments) {
        this.isAttachmentsDragOver = false;
        return;
      }
      this.isAttachmentsDragOver = true;
    },
    handleAttachmentsDragEnter() {
      if (!this.canEditAttachments) {
        this.isAttachmentsDragOver = false;
        return;
      }
      this.isAttachmentsDragOver = true;
    },
    handleAttachmentsDragLeave(event) {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        this.isAttachmentsDragOver = false;
      }
    },
    handleAttachmentsDrop(event) {
      this.isAttachmentsDragOver = false;
      if (!this.canEditAttachments) {
        showNotification(
          "You lack permission to upload files.",
          NOTIFICATION_TYPES.warning
        );
        return;
      }
      const files = Array.from(event.dataTransfer?.files || []);
      if (!files.length) {
        showNotification("No files selected.", NOTIFICATION_TYPES.warning);
        return;
      }
      this.uploadAttachments(files);
    },
    async uploadAttachments(files = []) {
      if (!files.length) {
        showNotification("No files selected.", NOTIFICATION_TYPES.warning);
        return;
      }
      const formData = new FormData();
      files.forEach((file) => formData.append(FORM_FIELDS.files, file));
      try {
        this.attachmentsBusy = true;
        const response = await axiosRef.post(
          apiUrl(REQUEST_API_ENDPOINTS.uploadFiles),
          formData,
          MULTIPART_FORM_HEADERS
        );
        if (response?.data?.success) {
          const ids = response.data.fileIds || [];
          this.attachmentsFileIds = [...this.attachmentsFileIds, ...ids];
          await this.fetchUploadedFilesDetails();
          await this.saveAttachmentsToRequest();
          await this.loadAttachments({ force: true });
          showNotification(
            "Files uploaded successfully.",
            NOTIFICATION_TYPES.success
          );
        } else {
          showNotification("File upload failed.", NOTIFICATION_TYPES.error);
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.attachmentsBusy = false;
      }
    },
    async fetchUploadedFilesDetails() {
      if (!this.attachmentsFileIds.length) {
        this.attachmentsFiles = [];
        return;
      }
      try {
        const response = await axiosRef.get(
          apiUrl(REQUEST_API_ENDPOINTS.filesAfterUpload),
          {
            params: {
              file_ids: JSON.stringify(this.attachmentsFileIds)
            }
          }
        );
        if (response?.data?.success) {
          const data = response.data.data || [];
          this.attachmentsFiles = data.map((file) => ({
            id: file?.id,
            name: file?.name,
            size: file?.size ?? null,
            path: file?.path
          }));
        }
      } catch (error) {
        handleError(error);
      }
    },
    removeAttachment(file) {
      if (!file?.id) return;
      if (!this.canEditAttachments) return;
      this.attachmentsFileIds = this.attachmentsFileIds.filter(
        (id) => id !== file.id
      );
      this.attachmentsFiles = this.attachmentsFiles.filter(
        (entry) => entry.id !== file.id
      );
      this.saveAttachmentsToRequest();
    },
    async saveAttachmentsToRequest() {
      if (!this.requestContext?.id) return;
      const requestId = this.requestContext.id;
      const payload = {
        [REQUEST_DATA_FIELDS.costUnit]:
          this.attachmentsRequestDetails?.[REQUEST_DATA_FIELDS.costUnit] ??
          null,
        [REQUEST_DATA_FIELDS.description]: (
          this.attachmentsRequestDetails?.[REQUEST_DATA_FIELDS.description] ||
          ""
        ).trim(),
        records: this.attachmentsRecords,
        files: this.attachmentsFileIds
      };
      const formData = new FormData();
      formData.append(FORM_FIELDS.data, JSON.stringify(payload));
      try {
        this.attachmentsBusy = true;
        const response = await axiosRef.post(
          apiUrl(REQUEST_API_ENDPOINTS.requestEdit(requestId)),
          formData,
          MULTIPART_FORM_HEADERS
        );
        if (response?.data?.success) {
          this.$emit("refresh");
        } else {
          showNotification("Request update failed.", NOTIFICATION_TYPES.error);
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.attachmentsBusy = false;
      }
    },
    downloadAttachment(file) {
      if (!file?.path) {
        showNotification(
          "Download link unavailable for this file.",
          NOTIFICATION_TYPES.warning
        );
        return;
      }
      const path = String(file.path || "");
      const url = path.startsWith("http") ? path : `${urlStringStart}${path}`;
      axiosRef
        .get(url, { responseType: RESPONSE_TYPES.blob })
        .then((response) => {
          const blob = response?.data;
          if (!blob || blob.size === 0) {
            showNotification(
              "Downloaded file is empty.",
              NOTIFICATION_TYPES.warning
            );
            return;
          }
          const objectUrl = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = objectUrl;
          link.download = file.name || "request-file";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(objectUrl);
        })
        .catch((error) => {
          handleError(error);
        });
    }
  }
};
</script>

<style scoped>
.request-action-modal {
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.popup-overlay.drag-over {
  border: none;
}

.popup-overlay.drag-over::after {
  content: "";
  position: absolute;
  inset: 0;
  background-color: #00bfff36;
  border: 2px dashed #2196f3;
  pointer-events: none;
  z-index: 2;
}

.request-action-modal.attachments-modal {
  width: min(760px, 92vw);
  height: min(520px, 90vh);
  display: flex;
  flex-direction: column;
}

.request-action-modal.email-modal,
.request-action-modal.approval-modal {
  width: 520px;
  max-height: min(520px, 90vh);
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.email-modal .email-body,
.approval-modal .email-body {
  flex: 0 1 auto;
  overflow-y: auto;
}

.attachments-body {
  padding: 16px;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.files-section {
  border: 1px solid #d0d0d0;
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.files-header small {
  display: block;
  font-size: 11px;
  color: #6b7280;
}

.files-table-wrapper {
  width: 100%;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-top: 8px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: white;
}

.files-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 12px;
}

.files-table.files-table-empty {
  height: 100%;
}

.files-table th,
.files-table td {
  padding: 8px 12px;
  text-align: left;
  vertical-align: middle;
  line-height: 1.4;
}

.files-table th {
  border-bottom: 1px solid #d0d0d0;
}

.files-table .empty-cell {
  text-align: center;
  color: #7b7f89;
}

.files-table td.actions-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3px;
}

.files-table td.actions-cell button + button {
  margin-left: 4px;
}

.file-name-cell {
  max-width: 220px;
  display: flex;
  align-items: center;
}

.file-name-text {
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size-cell {
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-action {
  border: none;
  background: #e6eaef;
  color: #13415b;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-action.danger {
  background: #f3d6d6;
  color: #a3272b;
}

.hidden-input {
  display: none;
}

.upload-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.upload-label {
  min-width: 40px;
  font-size: 13px;
  color: #333;
}

.upload-input {
  flex: 1;
  height: 32px;
  padding: 6px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
  font-size: 13px;
}

.upload-drop-zone {
  border: 2px dashed #b3c2c1;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  color: #4b5563;
  background: #f8fbfb;
  transition:
    border-color 0.2s ease,
    background 0.2s ease;
}

.upload-drop-zone.active {
  border-color: #0f766e;
  background: #e8f2f1;
}

.drop-title {
  font-weight: 600;
  font-size: 14px;
}

.drop-subtitle {
  font-size: 12px;
  margin-top: 6px;
  color: #6b7280;
}

.filepaths-body {
  gap: 12px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.popup-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-grow: 1;
}

.popup-title-icon {
  width: 20px;
  height: 20px;
  opacity: 0.9;
  filter: brightness(0) invert(1);
}

.rocrate-modal {
  width: min(860px, 94vw);
  max-height: min(720px, 90vh);
  display: flex;
  flex-direction: column;
}

.rocrate-help-wrapper {
  position: relative;
  display: inline-flex;
  margin-right: 10px;
}

.rocrate-help-wrapper::after {
  content: "";
  position: absolute;
  top: 100%;
  right: 0;
  width: 120px;
  height: 18px;
  background: transparent;
}

.rocrate-help-button {
  min-width: 18px;
  min-height: 18px;
  border-radius: 0;
  border: none;
  background: transparent;
  color: #ffffff;
  font-size: 18px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.rocrate-help-popup {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: min(520px, calc(100vw - 32px));
  max-height: min(60vh, 520px);
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid #d7dee3;
  background: #ffffff;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.18);
  color: #44505f;
  display: none;
  z-index: 20;
}

.rocrate-help-popup::before {
  content: "";
  position: absolute;
  top: -7px;
  right: 14px;
  width: 14px;
  height: 14px;
  background: #ffffff;
  border-left: 1px solid #d7dee3;
  border-top: 1px solid #d7dee3;
  transform: rotate(45deg);
}

.rocrate-help-scroll {
  max-height: min(60vh, 520px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 14px;
  scrollbar-gutter: stable;
}

.rocrate-help-wrapper:hover .rocrate-help-popup,
.rocrate-help-wrapper:focus-within .rocrate-help-popup {
  display: block;
}

.rocrate-help-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.rocrate-help-title {
  font-size: 16px;
  font-weight: 700;
  color: #13415b;
  margin-bottom: 6px;
}

.rocrate-help-intro {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #4b5563;
}

.rocrate-help-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.rocrate-help-section {
  border: 1px solid #dbe4ea;
  border-radius: 12px;
  background: linear-gradient(180deg, #f9fbfc 0%, #f4f7f8 100%);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rocrate-help-section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #13415b;
}

.rocrate-help-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  font-size: 12px;
  line-height: 1.55;
  color: #44505f;
}

.rocrate-help-list strong {
  color: #13415b;
}

.rocrate-help-list a {
  color: #0f5c92;
  text-decoration: none;
}

.rocrate-help-list a:hover {
  text-decoration: underline;
}

@media (max-width: 920px) {
  .rocrate-help-popup {
    width: min(520px, calc(100vw - 32px));
  }
}

.rocrate-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: min(620px, calc(90vh - 120px));
  overflow-y: auto;
}

.rocrate-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(160px, 0.8fr);
  gap: 8px;
}

.rocrate-summary-card {
  border: 1px solid #dbe4ea;
  border-radius: 12px;
  background: linear-gradient(180deg, #f9fbfc 0%, #f4f7f8 100%);
  padding: 10px 12px;
  display: grid;
  gap: 4px;
  min-width: 0;
}

.rocrate-summary-card-wide {
  min-width: 0;
}

.rocrate-summary-card .label {
  font-weight: 700;
  color: #13415b;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.rocrate-summary-card .value {
  color: #44505f;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.4;
}

.rocrate-summary-count {
  font-size: 20px !important;
  line-height: 1;
  font-weight: 700;
  color: #13415b !important;
}

.rocrate-request-name {
  color: #13415b !important;
  font-size: 20px !important;
  font-weight: 600;
  line-height: 1;
}

@media (max-width: 760px) {
  .rocrate-summary {
    grid-template-columns: 1fr;
  }
}

.rocrate-intro,
.rocrate-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.rocrate-toolbar-actions,
.rocrate-footer-links,
.rocrate-footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rocrate-options-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.rocrate-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border: 1px solid #d3dbe2;
  border-radius: 10px;
  padding: 10px;
  background: #ffffff;
  cursor: pointer;
}

.rocrate-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  min-width: 18px;
  min-height: 18px;
  flex: 0 0 18px;
  margin-top: 2px;
  box-sizing: border-box;
}

.rocrate-option-content {
  display: grid;
  gap: 2px;
}

.rocrate-option-title {
  font-size: 13px;
  font-weight: 700;
  color: #13415b;
}

.rocrate-option-description {
  font-size: 12px;
  line-height: 1.5;
  color: #44505f;
}

.rocrate-validation {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #efc7c7;
  background: #fff4f4;
  color: #a3272b;
  font-size: 12px;
  line-height: 1.45;
}

.rocrate-footer {
  justify-content: space-between;
  align-items: center;
}

.rocrate-footer a {
  text-decoration: none;
}

.rocrate-footer-link {
  color: #333;
  white-space: nowrap;
  gap: 6px;
  padding: 8px 12px;
}

.rocrate-footer-link svg {
  flex-shrink: 0;
}

.filepaths-modal {
  width: min(1100px, 94vw);
  height: min(560px, 88vh);
}

.filepaths-request-name {
  padding: 8px 12px;
  border: 1px solid #cfcfcf;
  border-radius: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
  background: #ffffff;
  box-shadow: inset 0 1px 0 #f3f3f3;
}

.filepaths-request-name .label {
  font-weight: 600;
}

.filepaths-columns {
  display: flex;
  gap: 12px;
  flex: 1;
  width: 100%;
  min-height: 0;
}

.filepaths-column {
  flex: 1 1 0;
  min-width: 0;
  border: 1px solid #cfcfcf;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  background: #ffffff;
}

.filepaths-left {
  flex: 1;
}

.filepaths-right {
  flex: 1;
}

.filepaths-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.filepaths-os-select {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.filepaths-os-icon {
  width: 18px;
  height: 18px;
  opacity: 0.75;
}

.filepaths-select {
  height: 32px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 4px 8px;
  background: #ffffff;
}

.filepaths-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 0;
}

.filepaths-scroll {
  overflow-y: auto;
  max-height: 260px;
  padding-right: 4px;
}

.userpaths-scroll {
  overflow-y: auto;
  max-height: 260px;
  padding-right: 4px;
}

.filepaths-list-box {
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 10px;
  background: #ffffff;
  overflow-x: hidden;
}

.filepaths-row {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 6px;
  align-items: center;
  padding: 6px 0 12px;
  position: relative;
}

.filepaths-row::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 2px;
  height: 1px;
  background: #e2e2e2;
}

.filepaths-row:last-child {
  padding-bottom: 6px;
}

.filepaths-row:last-child::after {
  display: none;
}

.filepaths-key {
  font-weight: 600;
  text-transform: none;
}

.filepaths-value {
  background: none;
  border: none;
  text-align: left;
  color: #333;
  cursor: copy;
  font-size: 12px;
  white-space: normal;
  word-break: break-all;
}

.filepaths-value:hover {
  color: #0f5c84;
}

.filepaths-input {
  background: #fdfdfd;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  color: #333;
  cursor: copy;
  text-align: left;
  box-shadow: inset 0 1px 0 #f3f3f3;
}

.filepaths-md5 {
  display: block;
  margin-top: 4px;
  color: #5d7480;
  font-size: 11px;
  word-break: break-all;
}

.userpath-row {
  position: relative;
  grid-template-columns: 110px 1fr 56px;
  padding-right: 0;
  padding: 8px 0 12px;
}

.userpath-row::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 3px;
  height: 1px;
  background: #e2e2e2;
}

.userpath-row:last-child::after {
  display: none;
}

.userpath-icons {
  position: static;
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  margin-left: 8px;
}

.icon-button {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: none;
  background: #e6eaef;
  color: #13415b;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-button svg {
  width: 14px;
  height: 14px;
}

.icon-button.danger {
  background: #f3d6d6;
  color: #a3272b;
}

.userpath-form {
  border: 1px dashed #b3c2c1;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.userpath-form input {
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #d0d0d0;
}

.userpath-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.email-body {
  gap: 12px;
}

.email-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.email-field input,
.email-field textarea {
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 8px;
  font-size: 13px;
}

.email-field .input-error {
  border-color: #d14343 !important;
}

.email-field .field-error {
  margin-top: 4px;
  font-size: 12px;
  color: #b42318;
}

.email-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

@media (max-width: 760px) {
  .rocrate-options-grid {
    grid-template-columns: 1fr;
  }

  .rocrate-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .rocrate-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .rocrate-footer-links,
  .rocrate-footer-actions {
    width: 100%;
  }

  .rocrate-summary-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .rocrate-summary-row .label {
    min-width: 0;
  }
}

.confirm-message {
  font-size: 14px;
  color: #333;
}

.small {
  padding: 6px 12px;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  color: #6b7280;
  padding: 20px 0;
}
</style>
