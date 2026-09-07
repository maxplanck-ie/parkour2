<template>
  <div class="date-input-wrap" ref="rootEl">
    <input
      :id="id"
      type="text"
      inputmode="numeric"
      autocomplete="off"
      class="date-input-field"
      placeholder="YYYY.MM.DD"
      :required="required"
      :value="draft"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
      @keydown="onFieldKeydown"
    />
    <button
      type="button"
      class="date-input-toggle"
      :aria-expanded="open"
      aria-label="Choose date"
      @click="toggleCalendar"
    >
      <font-awesome-icon icon="fa-regular fa-calendar-days" />
    </button>
    <div
      v-show="open"
      ref="panelEl"
      class="date-input-panel"
      role="dialog"
      aria-modal="false"
      aria-label="Choose date"
      tabindex="-1"
      @keydown="onPanelKeydown"
    >
      <div class="date-input-panel-header">
        <button
          type="button"
          class="date-input-nav"
          aria-label="Previous month"
          @click="changeMonth(-1)"
        >
          <font-awesome-icon icon="fa-solid fa-angle-left" />
        </button>
        <span class="date-input-panel-title">{{ panelTitle }}</span>
        <button
          type="button"
          class="date-input-nav"
          aria-label="Next month"
          @click="changeMonth(1)"
        >
          <font-awesome-icon icon="fa-solid fa-angle-right" />
        </button>
      </div>
      <div class="date-input-weekdays">
        <span v-for="weekday in weekdayLabels" :key="weekday">{{
          weekday
        }}</span>
      </div>
      <div class="date-input-days">
        <button
          v-for="day in calendarDays"
          :key="day.iso"
          type="button"
          class="date-input-day"
          :class="{
            'date-input-day-muted': !day.inMonth,
            'date-input-day-selected': day.iso === modelValue
          }"
          @click="selectDay(day.iso)"
        >
          {{ day.day }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { formatDisplayDate, parseDisplayDate } from "../utilities/dateUtils";
import { focusFirstElement, trapFocus } from "../utilities/utilityFunctions";

const WEEKDAY_LABELS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const DAYS_IN_CALENDAR_GRID = 42;

const props = defineProps({
  modelValue: { type: String, default: "" },
  id: { type: String, default: undefined },
  required: { type: Boolean, default: false }
});
const emit = defineEmits(["update:modelValue"]);

function isoToLocalDate(isoString) {
  if (!isoString) return null;
  const parsed = new Date(`${isoString}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function toIso(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

const draft = ref(formatDisplayDate(isoToLocalDate(props.modelValue)));
const open = ref(false);
const rootEl = ref(null);
const panelEl = ref(null);
const previouslyFocusedElement = ref(null);

const today = new Date();
const viewYear = ref((isoToLocalDate(props.modelValue) || today).getFullYear());
const viewMonth = ref((isoToLocalDate(props.modelValue) || today).getMonth());

watch(
  () => props.modelValue,
  (newValue) => {
    draft.value = formatDisplayDate(isoToLocalDate(newValue));
    const anchor = isoToLocalDate(newValue) || today;
    viewYear.value = anchor.getFullYear();
    viewMonth.value = anchor.getMonth();
  }
);

// Auto-insert dots as the user types digits, e.g. "20260907" -> "2026.09.07".
function maskDigits(rawValue) {
  const digits = rawValue.replace(/\D/g, "").slice(0, 8);
  const parts = [digits.slice(0, 4), digits.slice(4, 6), digits.slice(6, 8)];
  return parts.filter(Boolean).join(".");
}

function onInput(event) {
  const masked = maskDigits(event.target.value);
  draft.value = masked;
  const iso = parseDisplayDate(masked);
  if (iso && iso !== props.modelValue) {
    emit("update:modelValue", iso);
  } else if (!masked && props.modelValue) {
    emit("update:modelValue", "");
  }
}

function onFocus() {
  closeCalendarKeepFocus();
}

function onBlur() {
  const iso = parseDisplayDate(draft.value);
  draft.value = iso ? formatDisplayDate(isoToLocalDate(iso)) : "";
  if (!iso && props.modelValue) {
    emit("update:modelValue", "");
  }
}

function onFieldKeydown(event) {
  if (event.key === "Escape" && open.value) {
    event.preventDefault();
    closeCalendar();
  }
}

function closeCalendarKeepFocus() {
  open.value = false;
}

function closeCalendar() {
  if (!open.value) return;
  open.value = false;
  const returnFocusTo = previouslyFocusedElement.value;
  previouslyFocusedElement.value = null;
  returnFocusTo?.focus?.();
}

function toggleCalendar() {
  if (open.value) {
    closeCalendar();
    return;
  }
  const anchor = isoToLocalDate(props.modelValue) || today;
  viewYear.value = anchor.getFullYear();
  viewMonth.value = anchor.getMonth();
  previouslyFocusedElement.value = document.activeElement;
  open.value = true;
  nextTick(() => focusFirstElement(panelEl.value));
}

function changeMonth(delta) {
  const next = new Date(viewYear.value, viewMonth.value + delta, 1);
  viewYear.value = next.getFullYear();
  viewMonth.value = next.getMonth();
}

function selectDay(iso) {
  emit("update:modelValue", iso);
  closeCalendar();
}

function onPanelKeydown(event) {
  if (event.key === "Escape") {
    event.preventDefault();
    closeCalendar();
    return;
  }
  trapFocus(event, panelEl.value);
}

function onDocumentMousedown(event) {
  if (!open.value) return;
  if (rootEl.value && !rootEl.value.contains(event.target)) {
    closeCalendarKeepFocus();
  }
}

watch(open, (isOpen) => {
  if (isOpen) {
    document.addEventListener("mousedown", onDocumentMousedown);
  } else {
    document.removeEventListener("mousedown", onDocumentMousedown);
  }
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocumentMousedown);
});

const weekdayLabels = WEEKDAY_LABELS;

const panelTitle = computed(() => {
  const monthName = new Date(viewYear.value, viewMonth.value, 1).toLocaleString(
    "default",
    { month: "long" }
  );
  return `${monthName} ${viewYear.value}`;
});

const calendarDays = computed(() => {
  const firstOfMonth = new Date(viewYear.value, viewMonth.value, 1);
  // Monday-first grid: shift Sunday (0) to the end of the week.
  const leadingBlanks = (firstOfMonth.getDay() + 6) % 7;
  const gridStart = new Date(firstOfMonth);
  gridStart.setDate(gridStart.getDate() - leadingBlanks);

  return Array.from({ length: DAYS_IN_CALENDAR_GRID }, (_, index) => {
    const cellDate = new Date(gridStart);
    cellDate.setDate(cellDate.getDate() + index);
    return {
      iso: toIso(cellDate),
      day: cellDate.getDate(),
      inMonth: cellDate.getMonth() === viewMonth.value
    };
  });
});
</script>

<style scoped>
.date-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.date-input-field {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  color: inherit;
  text-transform: inherit;
  padding: 0;
  width: 100%;
}

.date-input-toggle {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  padding: 0 2px 0 4px;
  display: flex;
  align-items: center;
}

.date-input-toggle:hover {
  opacity: 1;
}

.date-input-panel {
  text-transform: none;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 20;
  width: 220px;
  background: white;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px;
  font-family: var(--app-font-family);
}

.date-input-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-weight: bold;
}

.date-input-nav {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 2px 6px;
}

.date-input-weekdays,
.date-input-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  text-align: center;
}

.date-input-weekdays {
  font-size: 11px;
  color: #888;
  margin-bottom: 2px;
}

.date-input-day {
  border: none;
  background: transparent;
  border-radius: 4px;
  padding: 4px 0;
  font-size: 12px;
  cursor: pointer;
}

.date-input-day:hover {
  background: #f0f0f0;
}

.date-input-day-muted {
  color: #bbb;
}

.date-input-day-selected {
  background: #006c66;
  color: white;
}
</style>
