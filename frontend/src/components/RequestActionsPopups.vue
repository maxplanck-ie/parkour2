<template>
  <div v-if="activeAction === 'uploadSigned'" class="popup-overlay" :class="{ 'drag-over': isUploadDragOver }"
    tabindex="0" @keydown="handlePopupKeydown" @dragover.prevent="handleUploadDragOver"
    @dragenter.prevent="handleUploadDragEnter" @dragleave.prevent="handleUploadDragLeave"
    @drop.prevent="handleUploadDrop">
    <div class="popup-container request-action-modal" :style="{ width: '520px' }">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_upload_signed_request.svg" alt="" />
          <span>Upload file</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body">
        <div class="upload-row">
          <label class="upload-label">File:</label>
          <input class="upload-input" type="text" :value="uploadFileName" readonly placeholder="Select a file" />
          <button class="popup-button secondary" type="button" @click="triggerUploadInput">Select</button>
          <input ref="uploadInput" type="file" class="hidden-input" @change="handleUploadSelection" />
        </div>
        <div class="upload-drop-zone" :class="{ active: isUploadDragOver }">
          <div class="drop-title">Drag &amp; drop the signed request here</div>
          <div class="drop-subtitle">Accepted formats: PDF, DOCX</div>
        </div>
      </div>
      <div class="popup-footer">
        <button ref="defaultUploadButton" class="popup-button yes-button" type="button" :disabled="uploadBusy"
          @click="submitSignedRequest">
          <span v-if="uploadBusy">Uploading...</span>
          <span v-else>Upload</span>
        </button>
        <button class="popup-button secondary" type="button" @click="close">Cancel</button>
      </div>
    </div>
  </div>

  <div v-if="activeAction === 'filePaths'" class="popup-overlay" tabindex="0" @keydown="handlePopupKeydown">
    <div class="popup-container request-action-modal filepaths-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_view_file_paths.svg" alt="" />
          <span>File Paths</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body filepaths-body">
        <div class="filepaths-request-name">
          <span class="label">Request Name:</span>
          <span class="value">{{ requestContext?.name || '-' }}</span>
        </div>
        <div class="filepaths-columns">
          <div class="filepaths-column filepaths-left">
            <div class="filepaths-header">
              <span>Request File Paths:</span>
              <div class="filepaths-os-select" title="Change OS to format file paths">
                <font-awesome-icon class="filepaths-os-icon" icon="fa-solid fa-desktop" />
                <select v-model="selectedOS" class="filepaths-select">
                  <option value="Linux">Linux</option>
                  <option value="macOS">macOS</option>
                  <option value="Windows">Windows</option>
                </select>
              </div>
            </div>
            <div class="filepaths-list filepaths-list-box">
              <div class="filepaths-scroll">
                <div v-for="entry in formattedFilepaths" :key="entry.key" class="filepaths-row">
                  <div class="filepaths-key">{{ entry.key }}</div>
                  <button class="filepaths-value filepaths-input" type="button" @click="copyText(entry.value)">
                    {{ entry.value || 'Empty' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="filepaths-column filepaths-right">
            <div class="filepaths-header">
              <span>Request User Paths:</span>
              <button class="popup-button secondary small" type="button" @click="startAddUserPath"
                title="Add User Path">
                <font-awesome-icon icon="fa-solid fa-square-plus" />
                <span>Add</span>
              </button>
            </div>
            <div class="filepaths-list filepaths-list-box">
              <div class="userpaths-scroll">
                <div v-if="showUserPathForm" class="userpath-form">
                  <input v-model.trim="userPathForm.name" type="text" placeholder="Name" />
                  <input v-model.trim="userPathForm.value" type="text" placeholder="Path" />
                  <div class="userpath-actions">
                    <button class="popup-button yes-button small" type="button" :disabled="!canSaveUserPath"
                      @click="saveUserPath">Save</button>
                    <button class="popup-button small" type="button" @click="cancelUserPath">Cancel</button>
                  </div>
                </div>
                <div v-if="!hasUserPaths" class="empty-state">No User Paths</div>
                <div v-for="path in displayUserPaths" :key="path.id" class="filepaths-row userpath-row">
                  <div class="filepaths-key">{{ path.name }}</div>
                  <button class="filepaths-value filepaths-input userpath-value" type="button"
                    @click="copyText(path.value || 'Empty')">
                    {{ path.value || 'Empty' }}
                  </button>
                  <div class="userpath-icons">
                    <button class="icon-button" type="button" title="Edit" @click="startEditUserPath(path)">
                      <font-awesome-icon icon="fa-solid fa-pen" />
                    </button>
                    <button class="icon-button danger" type="button" title="Delete"
                      @click="confirmDeleteUserPath(path)">
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
        <button ref="defaultFilepathsButton" class="popup-button yes-button" type="button" @click="close">Close</button>
      </div>
    </div>
  </div>

  <div v-if="activeAction === 'composeEmail'" class="popup-overlay" tabindex="0" @keydown="handlePopupKeydown">
    <div class="popup-container request-action-modal" :style="{ width: '520px', height: '400px' }">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_compose_email.svg" alt="" />
          <span>New Email</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body email-body">
        <label class="email-field">
          <span>Subject:</span>
          <input v-model="emailForm.subject" type="text" placeholder="Subject" />
        </label>
        <label class="email-field">
          <span>Message:</span>
          <textarea v-model="emailForm.message" rows="6" placeholder="Message"></textarea>
        </label>
        <label class="email-checkbox">
          <input type="checkbox" v-model="emailForm.includeFailed" />
          <span>Include the list of all failed libraries and samples</span>
        </label>
      </div>
      <div class="popup-footer">
        <button ref="defaultComposeButton" class="popup-button yes-button with-icon" type="button" :disabled="emailBusy"
          @click="sendEmail">
          <font-awesome-icon icon="fa-solid fa-paper-plane" />
          <span>{{ emailBusy ? 'Sending...' : 'Send' }}</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="activeAction === 'solicitApproval'" class="popup-overlay" tabindex="0" @keydown="handlePopupKeydown">
    <div class="popup-container request-action-modal" :style="{ width: '520px', height: '400px' }">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_solicit_approval.svg" alt="" />
          <span>New Email for Approval Solicitation</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body email-body">
        <label class="email-field">
          <span>Subject:</span>
          <input v-model="approvalForm.subject" type="text" placeholder="Subject" />
        </label>
        <label class="email-field">
          <span>Message:</span>
          <textarea v-model="approvalForm.message" rows="6" placeholder="Message"></textarea>
        </label>
        <label class="email-checkbox">
          <input type="checkbox" v-model="approvalForm.includeRecords" />
          <span>Include the list of all libraries and samples</span>
        </label>
      </div>
      <div class="popup-footer">
        <button ref="defaultApprovalButton" class="popup-button yes-button with-icon" type="button"
          :disabled="approvalBusy" @click="sendApprovalEmail">
          <font-awesome-icon icon="fa-solid fa-paper-plane" />
          <span>{{ approvalBusy ? 'Sending...' : 'Send' }}</span>
        </button>
      </div>
    </div>
  </div>

  <div v-if="activeAction === 'deleteRequest'" class="popup-overlay" tabindex="0" @keydown="handlePopupKeydown">
    <div class="popup-container request-action-modal" :style="{ width: '420px' }">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_delete_request.svg" alt="" />
          <span>Delete Request</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body">
        <div class="confirm-message">
          Are you sure that you want to delete the request "{{ requestContext?.name }}"?
        </div>
      </div>
      <div class="popup-footer">
        <button ref="defaultDeleteButton" class="popup-button yes-button" type="button" :disabled="deleteBusy"
          @click="confirmDelete">
          <span v-if="deleteBusy">Deleting...</span>
          <span v-else>Delete</span>
        </button>
        <button class="popup-button secondary" type="button" @click="close">Cancel</button>
      </div>
    </div>
  </div>

  <div v-if="activeAction === 'attachments'" class="popup-overlay" :class="{ 'drag-over': isAttachmentsDragOver }"
    tabindex="0" @keydown="handlePopupKeydown" @dragover.prevent="handleAttachmentsDragOver"
    @dragenter.prevent="handleAttachmentsDragEnter" @dragleave.prevent="handleAttachmentsDragLeave"
    @drop.prevent="handleAttachmentsDrop">
    <div class="popup-container request-action-modal attachments-modal">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_attachments.svg" alt="" />
          <span>Attachments</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body attachments-body">
        <div class="files-section">
          <div class="files-header">
            <div>
              <span>Files</span>
              <small>Upload request related documents.</small>
            </div>
            <button v-if="canEditAttachments" class="header-button ghost" type="button"
              :disabled="attachmentsBusy" @click="triggerAttachmentsUpload">
              <font-awesome-icon icon="fa-solid fa-square-plus" style="color: white" />
              <span>Add Files</span>
            </button>
            <input ref="attachmentsFileInput" type="file" multiple @change="handleAttachmentsSelection"
              style="display: none" />
          </div>
          <div class="files-table-wrapper">
            <table class="files-table" :class="{ 'files-table-empty': !attachmentsFiles.length }">
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
                    <span class="file-name-text" :title="file.name">{{ file.name }}</span>
                  </td>
                  <td class="file-size-cell" :title="formatFileSize(file.size)">
                    {{ formatFileSize(file.size) }}
                  </td>
                  <td class="actions-cell">
                    <button type="button" class="icon-action"
                      :title="file.path ? `Download ${file.name}` : 'Download unavailable'" :disabled="!file.path"
                      @click="downloadAttachment(file)">
                      <font-awesome-icon icon="fa-solid fa-download" />
                    </button>
                    <button v-if="canEditAttachments" type="button" class="icon-action danger"
                      :title="`Remove ${file.name}`" :disabled="attachmentsBusy" @click="removeAttachment(file)">
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
        <button ref="defaultAttachmentsButton" class="popup-button yes-button" type="button"
          :disabled="attachmentsBusy" @click="close">Close</button>
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
      uploadFile: null,
      isUploadDragOver: false,
      uploadBusy: false,
      filepaths: {},
      userPaths: [],
      selectedOS: "Linux",
      showUserPathForm: false,
      userPathForm: {
        mode: "add",
        id: null,
        name: "",
        value: ""
      },
      emailForm: {
        subject: "",
        message: "",
        includeFailed: false
      },
      approvalForm: {
        subject: "",
        message: "",
        includeRecords: true
      },
      emailBusy: false,
      approvalBusy: false,
      deleteBusy: false,
      attachmentsFiles: [],
      attachmentsFileIds: [],
      attachmentsBusy: false,
      isAttachmentsDragOver: false,
      attachmentsRequestDetails: {
        cost_unit: null,
        description: ""
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
        const formatted =
          key === "data" || key === "metadata"
            ? this.formatPathForOS(rawValue)
            : rawValue || "";
        entries.push({ key, value: formatted });
      });
      return entries;
    },
    hasUserPaths() {
      return this.userPaths.some(
        (item) => item.value !== null && item.value !== ""
      );
    },
    displayUserPaths() {
      return this.hasUserPaths ? this.userPaths : [];
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
  beforeDestroy() {
    document.removeEventListener("keydown", this.handleGlobalKeydown);
  },
  watch: {
    activeAction(newVal) {
      if (!newVal) return;
      this.resetStateForAction(newVal);
      if (newVal === "filePaths") {
        this.fetchFilepaths();
      }
      if (newVal === "composeEmail") {
        this.emailForm.subject = this.requestContext?.name || "";
        this.emailForm.message = "";
        this.emailForm.includeFailed = false;
      }
      if (newVal === "solicitApproval") {
        this.approvalForm.subject = this.requestContext?.name || "";
        this.approvalForm.message = "";
        this.approvalForm.includeRecords = true;
      }
      if (newVal === "attachments") {
        this.loadAttachments();
      }

      this.$nextTick(() => {
        const focusMap = {
          uploadSigned: "defaultUploadButton",
          filePaths: "defaultFilepathsButton",
          deleteRequest: "defaultDeleteButton",
          attachments: "defaultAttachmentsButton"
        };
        const refName = focusMap[newVal];
        if (refName && this.$refs[refName]?.focus) {
          this.$refs[refName].focus();
        }
      });
    },
    requestContext() {
      if (this.activeAction === "composeEmail") {
        this.emailForm.subject = this.requestContext?.name || "";
      }
      if (this.activeAction === "solicitApproval") {
        this.approvalForm.subject = this.requestContext?.name || "";
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
        if (this.activeAction === "composeEmail" || this.activeAction === "solicitApproval") {
          return;
        }
        event.preventDefault();
        if (this.activeAction === "uploadSigned") {
          if (!this.uploadBusy) this.submitSignedRequest();
          return;
        }
        if (this.activeAction === "deleteRequest") {
          if (!this.deleteBusy) this.confirmDelete();
          return;
        }
        if (this.activeAction === "filePaths") {
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
      this.userPathForm = { mode: "add", id: null, name: "", value: "" };
      this.emailBusy = false;
      this.approvalBusy = false;
      this.deleteBusy = false;
      this.attachmentsFiles = [];
      this.attachmentsFileIds = [];
      this.attachmentsBusy = false;
      this.isAttachmentsDragOver = false;
      this.attachmentsRequestDetails = { cost_unit: null, description: "" };
      this.attachmentsRecords = [];
      if (action === "filePaths") {
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
        showNotification("No file selected.", "warning");
        return;
      }
      const formData = new FormData();
      formData.append("file", this.uploadFile);
      try {
        this.uploadBusy = true;
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestContext.id}/upload_deep_sequencing_request/`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        if (response?.data?.success) {
          showNotification(
            "Signed request uploaded successfully.",
            "success"
          );
          this.$emit("refresh");
          this.close();
        } else {
          showNotification("Signed request upload failed.", "error");
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
          `${urlStringStart}/api/requests/${this.requestContext.id}/`
        );
        const data = response?.data || {};
        this.filepaths = data.filepaths || {};
        const metapaths = data.metapaths || {};
        this.userPaths = Object.entries(metapaths).map(([name, value], index) => ({
          id: index + 1,
          name,
          value
        }));
      } catch (error) {
        handleError(error);
      }
    },
    formatPathForOS(filepath) {
      const filepathRegex =
        /^\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_\/.]+$/;
      if (!filepath) {
        return "Empty";
      }
      if (filepathRegex.test(filepath)) {
        const filepathSplit = filepath.split("/").filter((item) => item !== "");
        if (this.selectedOS === "Windows") {
          return `\\\\${filepathSplit[0]}\\${filepathSplit[1]}-${filepathSplit[2]}\\${filepathSplit
            .slice(3)
            .join("\\")}`;
        }
        if (this.selectedOS === "macOS") {
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
        return "macOS";
      }
      if (/Windows NT/.test(userAgent)) {
        return "Windows";
      }
      return "Linux";
    },
    async copyText(text) {
      try {
        await navigator.clipboard.writeText(text || "");
        showNotification("Path copied to clipboard.", "success");
      } catch (error) {
        showNotification("Path copy failed.", "error");
      }
    },
    startAddUserPath() {
      this.showUserPathForm = true;
      this.userPathForm = { mode: "add", id: null, name: "", value: "" };
    },
    startEditUserPath(path) {
      this.showUserPathForm = true;
      this.userPathForm = {
        mode: "edit",
        id: path.id,
        name: path.name,
        value: path.value
      };
    },
    cancelUserPath() {
      this.showUserPathForm = false;
      this.userPathForm = { mode: "add", id: null, name: "", value: "" };
    },
    async saveUserPath() {
      if (!this.canSaveUserPath) return;
      const newName = this.userPathForm.name;
      const newValue = this.userPathForm.value;
      const current = this.userPaths.slice();
      const map = new Map();

      if (this.userPathForm.mode === "add") {
        if (current.some((item) => item.name === newName)) {
          showNotification(
            "User path name already exists.",
            "warning"
          );
          return;
        }
        map.set(newName, newValue);
        current.forEach((item) => {
          if (item.value !== null) map.set(item.name, item.value);
        });
      } else {
        current.forEach((item) => {
          if (item.id === this.userPathForm.id) {
            map.set(newName, newValue);
          } else {
            map.set(item.name, item.value);
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
          `${urlStringStart}/api/requests/${this.requestContext.id}/put_metapaths/`,
          userpaths
        );
        if (response?.data?.success) {
          showNotification("User path saved successfully.", "success");
          this.userPaths = Object.entries(userpaths).map(([name, value], index) => ({
            id: index + 1,
            name,
            value
          }));
          this.showUserPathForm = false;
        } else {
          showNotification("User path save failed.", "error");
        }
      } catch (error) {
        handleError(error);
      }
    },
    async sendEmail() {
      if (!this.requestContext?.id) return;
      if (!this.emailForm.subject || !this.emailForm.message) {
        showNotification("All fields are required.", "warning");
        return;
      }
      const formData = new FormData();
      formData.append("subject", this.emailForm.subject);
      formData.append("message", this.emailForm.message);
      formData.append("include_failed_records", String(this.emailForm.includeFailed));
      try {
        this.emailBusy = true;
        await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestContext.id}/send_email/`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        showNotification("Email sent successfully.", "success");
        this.close();
      } catch (error) {
        handleError(error);
      } finally {
        this.emailBusy = false;
      }
    },
    async sendApprovalEmail() {
      if (!this.requestContext?.id) return;
      if (!this.approvalForm.subject || !this.approvalForm.message) {
        showNotification("All fields are required.", "warning");
        return;
      }
      const formData = new FormData();
      formData.append("subject", this.approvalForm.subject);
      formData.append("message", this.approvalForm.message);
      formData.append("include_records", String(this.approvalForm.includeRecords));
      try {
        this.approvalBusy = true;
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestContext.id}/solicit_approval/`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        if (response?.data?.success) {
          showNotification("Approval email sent to PI.", "success");
          this.close();
        } else {
          showNotification("Approval email failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.approvalBusy = false;
      }
    },
    async confirmDelete() {
      if (!this.requestContext?.id) return;
      try {
        this.deleteBusy = true;
        const response = await axiosRef.delete(
          `${urlStringStart}/api/requests/${this.requestContext.id}/`
        );
        if (response?.status === 204 || response?.data?.success) {
          showNotification("Request deleted successfully.", "success");
          this.$emit("refresh");
          this.close();
        } else {
          showNotification("Request deletion failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.deleteBusy = false;
      }
    },
    formatFileSize(size) {
      if (size === undefined || size === null) return "-";
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
    async loadAttachments() {
      if (!this.requestContext?.id) return;
      const meta = this.requestContext?.meta || null;
      const records = Array.isArray(this.requestContext?.records)
        ? this.requestContext.records
        : [];

      if (meta) {
        const filesList = Array.isArray(meta?.files) ? meta.files : [];
        this.attachmentsFiles = filesList.map((file) => ({
          id: file?.id ?? file?.pk,
          name: file?.name,
          size: file?.size,
          path: file?.path
        }));
        this.attachmentsFileIds = this.attachmentsFiles
          .map((file) => file?.id)
          .filter((id) => id !== undefined && id !== null);

        this.attachmentsRequestDetails = {
          cost_unit: meta?.cost_unit ?? null,
          description: meta?.description ?? ""
        };
      }

      if (records.length) {
        this.attachmentsRecords = records
          .filter((record) => record?.pk && record?.record_type)
          .map((record) => ({
            pk: record.pk,
            record_type: record.record_type
          }));
      }

      const needsRequest =
        !meta ||
        this.attachmentsRequestDetails.cost_unit === null ||
        this.attachmentsRequestDetails.description === "";
      const needsRecords = !this.attachmentsRecords.length;

      if (!needsRequest && !needsRecords) {
        return;
      }

      this.attachmentsBusy = true;
      try {
        const requestId = this.requestContext.id;
        const [requestRes, recordsRes] = await Promise.allSettled([
          needsRequest
            ? axiosRef.get(`${urlStringStart}/api/requests/${requestId}/`)
            : Promise.resolve({ data: meta }),
          needsRecords
            ? axiosRef.get(`${urlStringStart}/api/requests/${requestId}/get_records/`)
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
            size: file?.size,
            path: file?.path
          }));
          this.attachmentsFileIds = this.attachmentsFiles
            .map((file) => file?.id)
            .filter((id) => id !== undefined && id !== null);
          this.attachmentsRequestDetails = {
            cost_unit: requestData?.cost_unit ?? null,
            description: requestData?.description ?? ""
          };
        }

        if (needsRecords) {
          const recordsData =
            recordsRes.status === "fulfilled" ? recordsRes.value?.data || [] : [];
          this.attachmentsRecords = Array.isArray(recordsData)
            ? recordsData
              .filter((record) => record?.pk && record?.record_type)
              .map((record) => ({
                pk: record.pk,
                record_type: record.record_type
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
        showNotification("You lack permission to upload files.", "warning");
        return;
      }
      const files = Array.from(event.dataTransfer?.files || []);
      if (!files.length) {
        showNotification("No files selected.", "warning");
        return;
      }
      this.uploadAttachments(files);
    },
    async uploadAttachments(files = []) {
      if (!files.length) {
        showNotification("No files selected.", "warning");
        return;
      }
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      try {
        this.attachmentsBusy = true;
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/upload_files/`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        if (response?.data?.success) {
          const ids = response.data.fileIds || [];
          this.attachmentsFileIds = [...this.attachmentsFileIds, ...ids];
          await this.fetchUploadedFilesDetails();
          await this.saveAttachmentsToRequest();
          showNotification("Files uploaded successfully.", "success");
        } else {
          showNotification("File upload failed.", "error");
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
          `${urlStringStart}/api/requests/get_files_after_upload/`,
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
            size: file?.size,
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
        cost_unit: this.attachmentsRequestDetails?.cost_unit ?? null,
        description: (this.attachmentsRequestDetails?.description || "").trim(),
        records: this.attachmentsRecords,
        files: this.attachmentsFileIds
      };
      const formData = new FormData();
      formData.append("data", JSON.stringify(payload));
      try {
        this.attachmentsBusy = true;
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${requestId}/edit/`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        if (response?.data?.success) {
          this.$emit("refresh");
        } else {
          showNotification("Request update failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.attachmentsBusy = false;
      }
    },
    downloadAttachment(file) {
      if (!file?.path) {
        showNotification("Download link unavailable for this file.", "warning");
        return;
      }
      const path = String(file.path || "");
      const url = path.startsWith("http") ? path : `${urlStringStart}${path}`;
      axiosRef
        .get(url, { responseType: "blob" })
        .then((response) => {
          const blob = response?.data;
          if (!blob || blob.size === 0) {
            showNotification("Downloaded file is empty.", "warning");
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
}

.popup-overlay.drag-over::after {
  content: "";
  position: fixed;
  inset: 0;
  background: rgba(15, 118, 110, 0.08);
  border: 2px dashed #0f766e;
  pointer-events: none;
  z-index: 1;
}

.request-action-modal.attachments-modal {
  width: min(760px, 92vw);
  height: min(520px, 90vh);
  display: flex;
  flex-direction: column;
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

.files-table td.actions-cell button+button {
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
  transition: border-color 0.2s ease, background 0.2s ease;
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

.email-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
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
