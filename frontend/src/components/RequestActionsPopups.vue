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

  <div v-if="activeAction === 'markComplete'" class="popup-overlay" tabindex="0" @keydown="handlePopupKeydown">
    <div class="popup-container request-action-modal" :style="{ width: '460px' }">
      <div class="popup-header">
        <div class="popup-title">
          <img class="popup-title-icon" src="@/assets/icons/action_mark_complete.svg" alt="" />
          <span>Mark request as complete</span>
        </div>
        <button class="popup-close-button" type="button" @click="close">&times;</button>
      </div>
      <div class="popup-body">
        <div class="confirm-message">{{ markCompleteMessage }}</div>
      </div>
      <div class="popup-footer">
        <button ref="defaultMarkCompleteButton" class="popup-button yes-button" type="button"
          :disabled="markCompleteBusy" @click="confirmMarkComplete">
          <span v-if="markCompleteBusy">Working...</span>
          <span v-else>{{ markCompleteButtonLabel }}</span>
        </button>
        <button class="popup-button secondary" type="button" @click="close">Cancel</button>
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
      markCompleteBusy: false,
      markCompleteOverride: false,
      deleteBusy: false
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
    markCompleteMessage() {
      if (this.markCompleteOverride) {
        return "There are unsequenced libraries/samples related to this request. Do you want to mark it as complete anyway?";
      }
      return `Are you sure that you want to mark request "${this.requestContext?.name || ""
        }" as complete?`;
    },
    markCompleteButtonLabel() {
      return this.markCompleteOverride ? "Still Continue" : "Yes";
    }
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

      this.$nextTick(() => {
        const focusMap = {
          uploadSigned: "defaultUploadButton",
          filePaths: "defaultFilepathsButton",
          markComplete: "defaultMarkCompleteButton",
          deleteRequest: "defaultDeleteButton"
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
        if (this.activeAction === "markComplete") {
          if (!this.markCompleteBusy) this.confirmMarkComplete();
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
      this.markCompleteBusy = false;
      this.markCompleteOverride = false;
      this.deleteBusy = false;
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
    async confirmMarkComplete() {
      if (!this.requestContext?.id) return;
      try {
        this.markCompleteBusy = true;
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestContext.id}/mark_as_complete/`,
          {
            data: JSON.stringify({
              override: this.markCompleteOverride ? "True" : "False"
            })
          }
        );
        if (response?.data?.success) {
          showNotification("Request marked as complete.", "success");
          this.$emit("refresh");
          this.close();
        } else if (response?.data?.noncomplete && !this.markCompleteOverride) {
          this.markCompleteOverride = true;
        } else {
          showNotification("Request update failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.markCompleteBusy = false;
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
    }
  }
};
</script>

<style scoped>
.request-action-modal {
  overflow: hidden;
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
