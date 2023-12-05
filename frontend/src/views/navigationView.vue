<template>
  <div style="height: 100vh; display: flex; flex-direction: column">
    <div
      class="bg-color-beige"
      id="header"
      style="
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        filter: drop-shadow(0.05rem 0.05rem 0.125rem #4b484880);
      "
    >
      <div style="display: flex; align-items: center">
        <div
          class="bg-color-mpg-green color-white"
          style="
            overflow: hidden;
            width: 290px;
            height: 70px;
            padding: 10px;
            transition: width 0.3s ease-in-out;
          "
          :style="{ width: collapseNavigation ? '75px' : '290px' }"
        >
          <font-awesome-icon
            style="font-size: 20px"
            icon="fa-solid fa-dna"
            size="xl"
          />
          <span
            :class="{
              'display-none': collapseNavigation,
              'text-large': !collapseNavigation,
            }"
            style="
              font-size: 18px;
              font-weight: bold;
              margin-left: 5px;
              overflow: hidden;
            "
          >
            Parkour LIMS
          </span>
        </div>
        <div
          class="color-bluish-grey cursor-pointer"
          style="font-size: 16px; margin-left: 20px"
          @click="toggleCollapse"
        >
          <font-awesome-icon
            icon="fa-solid fa-navicon"
            class="color-bluish-grey cursor-pointer"
            style="font-size: 16px"
            v-tooltip="
              collapseNavigation
                ? 'Expand Navigation Bar'
                : 'Collapse Navigation Bar'
            "
          />
        </div>
      </div>
      <div style="display: flex; align-items: center">
        <div
          class="color-bluish-grey"
          style="font-weight: bold; font-size: 14px; margin-right: 18px"
        >
          Saurabh Dome
        </div>
        <div
          class="cursor-default"
          style="color: #29485d50; font-weight: 500; margin-right: 18px"
        >
          |
        </div>

        <ul class="list-style-none" style="display: flex">
          <li
            v-for="item in headerItems"
            :key="item.id"
            style="margin-right: 18px"
            v-tooltip="item.name"
          >
            <div>
              <a class="no-focus-highlight" :href="item.url" target="_blank">
                <font-awesome-icon
                  class="color-bluish-grey"
                  style="font-size: 16px"
                  :icon="item.icon"
                />
              </a>
            </div>
          </li>
        </ul>
      </div>
    </div>
    <div style="flex: 1 1 auto; display: flex">
      <div
        class="bg-color-beige"
        id="navigation-bar"
        style="
          flex: 0 0 auto;
          overflow: hidden;
          width: 290px;
          transition: width 0.3s ease-in-out;
        "
        :style="{ width: collapseNavigation ? '75px' : '290px' }"
      >
        <ul class="list-style-none">
          <li
            v-for="item in navigationItems"
            :key="item.id"
            :id="item.id"
            @click="changeNavigation(item)"
            class="navigation-hover-item"
            :class="{
              'navigation-selected-item': currentNavigation === item.url,
            }"
          >
            <div
              class="bg-color-beige color-bluish-grey"
              style="
                height: 60px;
                width: 290px;
                padding: 0 16px;
                display: flex;
                align-items: center;
                justify-content: flex-start;
              "
            >
              <font-awesome-icon
                style="font-size: 18px"
                :icon="item.icon"
                size="xl"
              />
              <span
                class="text-large"
                style="font-size: 15px; font-weight: bold; margin-left: 20px"
                v-if="!collapseNavigation"
              >
                {{ item.name }}
              </span>
            </div>
          </li>
        </ul>
      </div>
      <div style="flex: 1 1 auto; background: #eeeeee">
        <div class="navigation-page" style="height: 100%; display: flex">
          <iframe
            :src="'http://localhost:9980/' + currentNavigation"
            scrolling="no"
            frameborder="0"
            style="width: 100%; border: none"
          ></iframe>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return {
      collapseNavigation: false,
      currentNavigation: "#requests",
      userData: {},
      navigationItems: [
        {
          id: "requests",
          name: "Requests",
          icon: "fa-solid fa-file-text",
          url: "#requests",
          children: [],
        },
        {
          id: "libraries-and-samples",
          name: "Libraries & Samples",
          icon: "fa-solid fa-flask",
          url: "#libraries",
          children: [],
        },
        {
          id: "incoming-libraries-and-samples",
          name: "Incoming Libraries & Samples",
          icon: "fa-solid fa-arrow-down",
          url: "#incoming-libraries",
          children: [],
        },
        {
          id: "index-generator",
          name: "Index Generator",
          icon: "fa-solid fa-cogs",
          url: "#index-generator",
          children: [],
        },
        {
          id: "preparation",
          name: "Preparation",
          icon: "fa-solid fa-table",
          url: "#preparation",
          children: [],
        },
        {
          id: "pooling",
          name: "Pooling",
          icon: "fa-solid fa-sort-amount-desc",
          url: "#pooling",
          children: [],
        },
        {
          id: "load-flowcell",
          name: "Load Flowcell",
          icon: "fa-solid fa-level-down",
          url: "#flowcells",
          children: [],
        },
        {
          id: "invoicing",
          name: "Invoicing",
          icon: "fa-solid fa-eur",
          url: "#invoicing",
          children: [],
        },
        {
          id: "usage",
          name: "Usage",
          icon: "fa-solid fa-pie-chart",
          url: "#usage",
          children: [],
        },
        {
          id: "statistics",
          name: "Statistics",
          icon: "fa-solid fa-line-chart",
          url: "",
          children: [
            {
              id: "statistics-runs",
              name: "Runs",
              icon: "",
              url: "#run-statistics",
            },
            {
              id: "statistics-sequences",
              name: "Sequences",
              icon: "",
              url: "#sequences-statistics",
            },
          ],
        },
      ],
      headerItems: [
        {
          id: "site-administration",
          name: "Site Administration",
          icon: "fa-cog",
          url: "admin",
        },
        {
          id: "documentation",
          name: "Documentation",
          icon: "fa-book",
          url: "https://github.com/maxplanck-ie/parkour2/wiki/Introduction",
        },
        {
          id: "duties",
          name: "Duties",
          icon: "fa-calendar",
          url: "vue/duties",
        },
        { id: "logout", name: "Logout", icon: "fa-sign-out", url: "logout" },
      ],
    };
  },
  methods: {
    toggleCollapse() {
      this.collapseNavigation = !this.collapseNavigation;
    },
    changeNavigation(item) {
      this.currentNavigation = item.url;
    },
  },
};
</script>
<style>
.header-username {
  font-weight: bold !important;
}

.x-treelist-item-tool,
.x-treelist-navigation .x-treelist-row-over > * > .x-treelist-item-icon {
  transition: all 0.2s ease-in-out;
}

.x-treelist-item-tool:hover,
.x-treelist-navigation .x-treelist-row-over > * > .x-treelist-item-icon {
  color: #006c66 !important;
  transform: scale(1.3);
}

.x-treelist-navigation .x-treelist-item-selected > .x-treelist-row,
.x-treelist-item-selected.x-treelist-item-tool,
.x-treelist-item-selected.x-treelist-item-expanded,
.x-treelist-item-tool:hover,
.x-treelist-row-over,
.x-treelist-item-expanded > ul > li {
  background-color: #dbdbd4 !important;
}

.x-treelist-navigation .x-treelist-item-floated > .x-treelist-row,
.x-treelist-item-tool,
.x-treelist-item-leaf,
.x-treelist-item-expandable {
  background-color: #ecebe5 !important;
}

.x-treelist-item-text,
.x-treelist-item-expander {
  color: #29485d !important;
  font-weight: bold !important;
}

.x-treelist-item-expanded > ul > li > div > div {
  margin-left: 22px !important;
}
</style>
