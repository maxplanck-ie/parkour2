<template>
  <div class="month-year-picker" :class="{ 'invalid-date': invalid }">
    <select
      :id="id"
      class="month-year-picker-month"
      :value="month"
      @change="onMonthChange($event.target.value)"
    >
      <option
        v-for="opt in monthOptions"
        :key="opt.value"
        :value="opt.value"
        :disabled="opt.disabled"
      >
        {{ opt.label }}
      </option>
    </select>
    <select
      class="month-year-picker-year"
      :value="year"
      @change="onYearChange($event.target.value)"
    >
      <option
        v-for="opt in yearOptions"
        :key="opt.value"
        :value="opt.value"
        :disabled="opt.disabled"
      >
        {{ opt.label }}
      </option>
    </select>
  </div>
</template>

<script>
const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec"
];

function pad2(n) {
  return String(n).padStart(2, "0");
}

export default {
  name: "MonthYearPicker",
  inheritAttrs: false,
  props: {
    id: {
      type: String,
      default: ""
    },
    // "YYYY-MM" string, same format as the native <input type="month">.
    modelValue: {
      type: String,
      required: true
    },
    // "YYYY-MM" string. Years/months after this are shown disabled.
    max: {
      type: String,
      default: ""
    },
    // Earliest selectable year (no need for a matching min month: Invoicing
    // History is only ever browsed forward from this year).
    minYear: {
      type: Number,
      default: 2000
    },
    invalid: {
      type: Boolean,
      default: false
    }
  },
  emits: ["update:modelValue"],
  computed: {
    year() {
      return Number(this.modelValue.slice(0, 4)) || new Date().getFullYear();
    },
    month() {
      return this.modelValue.slice(5, 7) || pad2(new Date().getMonth() + 1);
    },
    maxYear() {
      return this.max ? Number(this.max.slice(0, 4)) : null;
    },
    maxMonth() {
      return this.max ? this.max.slice(5, 7) : null;
    },
    yearOptions() {
      const currentYear = new Date().getFullYear();
      const topYear = Math.max(this.maxYear || currentYear, this.year);
      const options = [];
      for (let y = this.minYear; y <= topYear; y++) {
        options.push({
          value: String(y),
          label: String(y),
          disabled: this.maxYear !== null && y > this.maxYear
        });
      }
      return options;
    },
    monthOptions() {
      return MONTH_NAMES.map((label, index) => {
        const value = pad2(index + 1);
        const disabled =
          this.maxYear !== null &&
          this.year === this.maxYear &&
          this.maxMonth !== null &&
          value > this.maxMonth;
        return { value, label, disabled };
      });
    }
  },
  methods: {
    onMonthChange(value) {
      this.$emit("update:modelValue", `${this.year}-${value}`);
    },
    onYearChange(value) {
      let month = this.month;
      if (
        this.maxYear !== null &&
        Number(value) === this.maxYear &&
        this.maxMonth !== null &&
        month > this.maxMonth
      ) {
        month = this.maxMonth;
      }
      this.$emit("update:modelValue", `${value}-${month}`);
    }
  }
};
</script>

<style scoped>
.month-year-picker {
  display: flex;
  flex-direction: row;
  gap: 4px;
}

.month-year-picker select {
  padding: 3px 6px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 5px;
  height: 28px;
  line-height: 18px;
  color: #333;
  font-family: var(--app-font-family);
  font-size: 13px;
  background: #ffffff;
  outline: none;
  box-sizing: border-box;
  cursor: pointer;
}

.month-year-picker-month {
  width: 64px;
}

.month-year-picker-year {
  width: 68px;
}

.month-year-picker.invalid-date select {
  border: 1px solid #ff6b6b;
  background-color: #fff0f0;
}
</style>
