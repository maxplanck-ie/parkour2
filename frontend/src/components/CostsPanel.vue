<template>
  <div v-if="modelValue" class="costs-panel-overlay" @click.self.stop="close">
    <div
      ref="dialog"
      class="costs-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="costs-panel-title"
      tabindex="-1"
    >
      <div class="costs-panel-header">
        <span id="costs-panel-title" class="costs-panel-title">Costs</span>
        <button
          class="popup-close-button"
          type="button"
          aria-label="Close costs"
          @click="close"
        >
          &times;
        </button>
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
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in section.items" :key="row.id">
                <td class="costs-name-cell" :title="row.name">
                  {{ row.name }}
                </td>
                <td class="costs-price-cell">
                  {{ formatInvoicingCurrency(row.price) }}
                </td>
              </tr>
              <tr v-if="section.items.length === 0">
                <td colspan="2" class="costs-empty-row">No entries.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  focusFirstElement,
  trapFocus
} from "../utilities/utilityFunctions";
import { formatInvoicingCurrency } from "../constants/invoicingConsts";

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
      previouslyFocusedElement: null
    };
  },
  watch: {
    modelValue(isOpen) {
      if (isOpen) {
        this.previouslyFocusedElement = document.activeElement;
        this.fetchAllSections();
        this.$nextTick(() => focusFirstElement(this.$refs.dialog));
      }
    }
  },
  mounted() {
    document.addEventListener("click", this.handleDocumentClick);
    document.addEventListener("keydown", this.handleKeyDown);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  methods: {
    formatInvoicingCurrency,
    close() {
      this.$emit("update:modelValue", false);
      const returnFocusTo = this.previouslyFocusedElement;
      this.previouslyFocusedElement = null;
      this.$nextTick(() => returnFocusTo?.focus?.());
    },
    handleDocumentClick(event) {
      if (!this.modelValue) return;
      const dialog = this.$refs.dialog;
      if (dialog && !dialog.contains(event.target)) {
        this.close();
      }
    },
    handleKeyDown(event) {
      if (!this.modelValue) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.close();
        return;
      }
      trapFocus(event, this.$refs.dialog);
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

.costs-empty-row {
  text-align: center;
  color: #888;
  padding: 10px;
}
</style>
