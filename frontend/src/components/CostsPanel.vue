<template>
  <div v-if="modelValue" class="costs-panel-overlay" @click.self="close">
    <div class="costs-panel">
      <div class="costs-panel-header">
        <span class="costs-panel-title">Costs</span>
        <button class="popup-close-button" @click="close">&times;</button>
      </div>

      <div class="costs-panel-body">
        <div
          v-for="section in sections"
          :key="section.key"
          class="costs-section"
        >
          <div class="costs-section-title">{{ section.title }}</div>
          <div v-if="section.loading" class="costs-section-loading">
            Loading...
          </div>
          <table v-else class="costs-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Price</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in section.items" :key="row.id">
                <td class="costs-name-cell" :title="row.name">
                  {{ row.name }}
                </td>
                <td class="costs-price-cell">
                  <input
                    v-if="isEditing(section.key, row.id)"
                    v-model="editValue"
                    type="number"
                    min="0"
                    step="0.01"
                    class="costs-price-input"
                  />
                  <span v-else>{{ row.price }}</span>
                </td>
                <td class="costs-actions-cell">
                  <template v-if="isEditing(section.key, row.id)">
                    <button
                      class="costs-icon-button"
                      title="Save"
                      @click="requestSave(section, row)"
                    >
                      <font-awesome-icon icon="fa-solid fa-circle-check" />
                    </button>
                    <button
                      class="costs-icon-button"
                      title="Cancel"
                      @click="cancelEdit"
                    >
                      <font-awesome-icon icon="fa-solid fa-xmark" />
                    </button>
                  </template>
                  <button
                    v-else
                    class="costs-icon-button"
                    title="Edit price"
                    @click="startEdit(section.key, row)"
                  >
                    <font-awesome-icon icon="fa-solid fa-pen" />
                  </button>
                </td>
              </tr>
              <tr v-if="section.items.length === 0">
                <td colspan="3" class="costs-empty-row">No entries.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Confirmation dialog: every price edit must be explicitly confirmed
         before it is sent to the server; declining leaves the row in edit
         mode so the value can still be adjusted or cancelled outright. -->
    <div v-if="pendingConfirm" class="popup-overlay costs-confirm-overlay">
      <div class="popup-container" :style="{ width: '380px', height: 'auto' }">
        <div class="popup-header">
          <span class="popup-title">Confirm price change</span>
        </div>
        <div class="popup-body">
          <p>
            Change price for
            <strong>{{ pendingConfirm.row.name }}</strong>
            from <strong>{{ pendingConfirm.oldValue }}</strong> to
            <strong>{{ pendingConfirm.newValue }}</strong
            >?
          </p>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="confirmSave">
            Confirm
          </button>
          <button class="popup-button secondary" @click="cancelConfirm">
            Cancel
          </button>
        </div>
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

const SECTION_DEFS = [
  { key: "fixed_costs", title: "Fixed Costs", endpoint: "fixed_costs" },
  {
    key: "preparation_costs",
    title: "Preparation Costs",
    endpoint: "library_preparation_costs"
  },
  {
    key: "sequencing_costs",
    title: "Sequencing Costs",
    endpoint: "sequencing_costs"
  }
];

export default {
  name: "CostsPanel",
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ["update:modelValue"],
  data() {
    return {
      sections: SECTION_DEFS.map((def) => ({
        ...def,
        items: [],
        loading: false
      })),
      editingKey: null,
      editValue: "",
      editOriginalValue: "",
      pendingConfirm: null
    };
  },
  watch: {
    modelValue(isOpen) {
      if (isOpen) {
        this.cancelEdit();
        this.fetchAllSections();
      }
    }
  },
  methods: {
    close() {
      this.cancelEdit();
      this.$emit("update:modelValue", false);
    },
    async fetchAllSections() {
      await Promise.all(
        this.sections.map((section) => this.fetchSection(section))
      );
    },
    async fetchSection(section) {
      section.loading = true;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/${section.endpoint}/`
        );
        section.items = response.data || [];
      } catch (error) {
        handleError(error);
      } finally {
        section.loading = false;
      }
    },
    rowKey(sectionKey, rowId) {
      return `${sectionKey}:${rowId}`;
    },
    isEditing(sectionKey, rowId) {
      return this.editingKey === this.rowKey(sectionKey, rowId);
    },
    startEdit(sectionKey, row) {
      this.editingKey = this.rowKey(sectionKey, row.id);
      this.editValue = String(row.price);
      this.editOriginalValue = String(row.price);
    },
    // Discards the in-progress edit and rolls the row back to its
    // last-saved value; nothing is sent to the server.
    cancelEdit() {
      this.editingKey = null;
      this.editValue = "";
      this.editOriginalValue = "";
      this.pendingConfirm = null;
    },
    requestSave(section, row) {
      const newValue = Number(this.editValue);
      if (Number.isNaN(newValue) || newValue < 0) {
        showNotification(
          "Please enter a valid, non-negative price.",
          "warning"
        );
        return;
      }
      if (String(newValue) === this.editOriginalValue) {
        this.cancelEdit();
        return;
      }
      this.pendingConfirm = {
        section,
        row,
        oldValue: row.price,
        newValue
      };
    },
    // Declining the confirmation only closes the dialog — the row stays in
    // edit mode so the user can tweak the value again or hit Cancel to
    // fully roll back.
    cancelConfirm() {
      this.pendingConfirm = null;
    },
    async confirmSave() {
      const { section, row, newValue } = this.pendingConfirm;
      try {
        const response = await axiosRef.patch(
          `${urlStringStart}/api/${section.endpoint}/${row.id}/`,
          { price: newValue }
        );
        row.price = response.data?.price ?? newValue;
        showNotification("Price updated successfully.", "success");
        this.cancelEdit();
      } catch (error) {
        handleError(error);
        this.pendingConfirm = null;
      }
    }
  }
};
</script>

<style scoped>
.costs-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.costs-panel {
  width: 420px;
  max-width: 90vw;
  height: 100%;
  background: #fff;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  animation: costs-panel-slide-in 0.2s ease-out;
}

@keyframes costs-panel-slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.costs-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: linear-gradient(180deg, #0b7f78 0%, #006c66 100%);
}

.costs-panel-title {
  font-size: 16px;
  font-weight: bold;
  color: white;
}

.costs-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.costs-section {
  margin-bottom: 20px;
}

.costs-section-title {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 8px;
}

.costs-section-loading {
  color: #888;
  font-size: 13px;
}

.costs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.costs-table th {
  text-align: left;
  border-bottom: 1px solid #ddd;
  padding: 4px 6px;
  color: #666;
  font-weight: 600;
}

.costs-table td {
  border-bottom: 1px solid #f0f0f0;
  padding: 6px;
  vertical-align: middle;
}

.costs-name-cell {
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.costs-price-cell {
  width: 90px;
}

.costs-price-input {
  width: 80px;
  padding: 3px 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.costs-actions-cell {
  width: 60px;
  white-space: nowrap;
}

.costs-icon-button {
  background: none;
  border: none;
  cursor: pointer;
  color: #006c66;
  padding: 2px 4px;
}

.costs-icon-button:hover {
  color: #003f3b;
}

.costs-empty-row {
  text-align: center;
  color: #888;
  padding: 10px;
}

.costs-confirm-overlay {
  z-index: 1001;
}
</style>
