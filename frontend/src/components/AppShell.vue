<template>
  <div class="app-shell">
    <div class="app-shell-header">
      <div class="app-shell-brand">
        <img
          :src="iconLogo"
          alt="Parkour LIMS"
          class="statistics-header-icon"
        />
        <div class="header-title app-shell-title">
          <span class="app-shell-title-text">Parkour LIMS</span>
          <span v-if="instanceVersion" class="app-shell-version">{{
            instanceVersion
          }}</span>
        </div>
      </div>

      <div class="app-shell-bar">
        <nav class="app-shell-nav">
          <template v-for="node in navNodes" :key="node.text">
            <router-link
              v-if="node.leaf"
              :to="navPath(node)"
              class="app-shell-nav-link"
            >
              <font-awesome-icon
                v-if="navIcon(node)"
                :icon="navIcon(node)"
                class="app-shell-nav-icon"
              />
              <span>{{ node.text }}</span>
            </router-link>

            <div v-else class="app-shell-nav-dropdown">
              <button
                :id="`app-shell-dropdown-${node.text}`"
                class="app-shell-nav-link app-shell-nav-button"
                :aria-expanded="openDropdown === node.text"
                @click="toggleDropdown(node.text)"
              >
                <span>{{ node.text }}</span>
                <font-awesome-icon
                  icon="fa-solid fa-caret-down"
                  class="app-shell-nav-icon"
                />
              </button>
              <div
                v-if="openDropdown === node.text"
                class="app-shell-dropdown-menu"
              >
                <router-link
                  v-for="child in node.children"
                  :key="child.text"
                  :to="navPath(child)"
                  class="app-shell-dropdown-item"
                  @click="openDropdown = null"
                >
                  {{ child.text }}
                </router-link>
              </div>
            </div>
          </template>
        </nav>

        <div class="app-shell-user-actions">
          <span class="app-shell-username">{{ userName }}</span>
          <router-link
            v-if="isStaff"
            to="/duties"
            class="app-shell-icon-button"
            title="Duties"
          >
            <font-awesome-icon icon="fa-regular fa-calendar-days" />
          </router-link>
          <a
            v-if="isStaff"
            :href="`${urlStringStart}/admin`"
            class="app-shell-icon-button"
            title="Site Administration"
          >
            <font-awesome-icon icon="fa-solid fa-gear" />
          </a>
          <span class="app-shell-user-divider"></span>
          <button class="app-shell-icon-button" title="Logout" @click="logout">
            <font-awesome-icon icon="fa-solid fa-right-from-bracket" />
          </button>
        </div>
      </div>
    </div>

    <div class="app-shell-content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import {
  createAxiosObject,
  handleError,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { NAV_VIEW_TYPE_MAP } from "../constants/appShellConsts";
import iconLogo from "../assets/icons/parkour_logo_white.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "AppShell",
  data() {
    return {
      navNodes: [],
      userName: "",
      isStaff: false,
      instanceVersion: "",
      openDropdown: null,
      urlStringStart,
      iconLogo
    };
  },
  async mounted() {
    document.addEventListener("click", this.handleDocumentClick);
    document.addEventListener("keydown", this.handleKeyDown);
    await Promise.all([this.loadNavigationTree(), this.loadUserDetails()]);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  methods: {
    navPath(node) {
      return NAV_VIEW_TYPE_MAP[node.viewType]?.path || "/not_found";
    },
    navIcon(node) {
      return NAV_VIEW_TYPE_MAP[node.viewType]?.icon || null;
    },
    toggleDropdown(text) {
      this.openDropdown = this.openDropdown === text ? null : text;
    },
    handleDocumentClick(event) {
      if (!this.openDropdown) return;
      const target = event.target;
      if (target.closest(`#app-shell-dropdown-${this.openDropdown}`)) return;
      if (target.closest(".app-shell-dropdown-menu")) return;
      this.openDropdown = null;
    },
    handleKeyDown(event) {
      if (event.key === "Escape") {
        this.openDropdown = null;
      }
    },
    async loadNavigationTree() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/get_navigation_tree`
        );
        this.navNodes = response.data?.children || [];
      } catch (error) {
        handleError(error);
      }
    },
    async loadUserDetails() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api_user_details`
        );
        const payload = response.data?.USER;
        const user =
          typeof payload === "string" ? JSON.parse(payload) : payload;
        this.userName = user?.name || "";
        this.isStaff = user?.is_staff === true;
        this.instanceVersion = response.data?.INSTANCE_VERSION || "";
      } catch (error) {
        handleError(error);
      }
    },
    async logout() {
      try {
        await axiosRef.post(`${urlStringStart}/logout/`);
      } finally {
        window.location.href = `${urlStringStart}/login/`;
      }
    }
  }
};
</script>

<style scoped>
.app-shell {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.app-shell-header {
  margin: 10px 10px 0;
  width: calc(100% - 20px);
  height: 70px;
  flex: 0 0 auto;
  display: flex;
  align-items: stretch;
  border-radius: 8px;
  overflow: hidden;
}

.app-shell-brand {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  padding: 16px 28px 16px 14px;
  background: linear-gradient(135deg, #0a8a82 0%, #006c66 50%, #00504c 100%);
}

.app-shell-title {
  flex: 0 0 auto;
  width: auto;
  white-space: nowrap;
  display: flex;
  flex-direction: column;
  color: white;
}

.app-shell-title-text {
  line-height: 1.2;
}

.app-shell-version {
  font-size: 12px;
  line-height: 1.2;
  opacity: 0.75;
  font-weight: normal;
}

.app-shell-bar {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 6px;
  padding: 8px 16px;
  background: var(--app-nav-bg);
}

.app-shell-nav {
  flex: 1;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.app-shell-nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 18px;
  color: #333;
  text-decoration: none;
  white-space: nowrap;
  background: white;
  border: 1px solid var(--app-nav-pill-border);
  font-size: 12px;
  cursor: pointer;
}

.app-shell-nav-icon {
  font-size: 14px;
}

.app-shell-nav-link:hover {
  border-color: #006c66;
}

.app-shell-nav-link.router-link-active {
  background: var(--app-nav-pill-active-bg);
  border-color: #006c66;
  color: #006c66;
  font-weight: 600;
}

.app-shell-nav-dropdown {
  position: relative;
}

.app-shell-dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  min-width: 200px;
  z-index: 20;
  overflow: hidden;
}

.app-shell-dropdown-item {
  display: block;
  padding: 8px 14px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
}

.app-shell-dropdown-item:hover {
  background: #f0f0f0;
}

.app-shell-user-actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 12px;
}

.app-shell-username {
  color: #006c66;
  font-weight: 600;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.app-shell-user-divider {
  width: 1px;
  height: 20px;
  background: var(--app-nav-pill-border);
}

.app-shell-icon-button {
  color: #555;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  text-decoration: none;
}

.app-shell-icon-button:hover {
  color: #006c66;
}

.app-shell-content {
  flex: 1;
  overflow: hidden;
}
</style>
