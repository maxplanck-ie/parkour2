<template>
  <div class="not-found-page">
    <section class="not-found-card">
      <div class="not-found-intro">
        <div class="status-group">
          <font-awesome-icon
            icon="fa-solid fa-circle-exclamation"
            class="status-badge"
            aria-hidden="true"
          />
          <span class="eyebrow">404</span>
        </div>
        <h1>The page you requested does not exist.</h1>
      </div>
      <p class="lead">
        The route may be outdated, mistyped, or no longer available in the Vue
        application.
      </p>

      <div class="route-panel">
        <span class="route-label">Requested location</span>
        <code>{{ requestedLocation }}</code>
      </div>

      <div class="actions">
        <button
          class="action-button primary-action"
          type="button"
          @click="goToLibraries"
        >
          Open Libraries &amp; Samples
        </button>
        <button
          class="action-button secondary-action"
          type="button"
          @click="goBack"
        >
          Go Back
        </button>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: "NotFoundView",

  computed: {
    requestedLocation() {
      return (
        this.$route.query.missingRoute ||
        this.$route.fullPath ||
        "/vue/not_found"
      );
    }
  },

  methods: {
    goToLibraries() {
      this.$router.push("/vue/libraries_and_samples");
    },

    goBack() {
      if (window.history.length > 1) {
        this.$router.back();
        return;
      }
      this.goToLibraries();
    }
  }
};
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

.not-found-page {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 18px 10px;
  background: linear-gradient(180deg, #f5f6f7 0%, #eef1f2 100%);
}

.not-found-card {
  width: min(760px, 100%);
  padding: 28px 30px;
  border: 1px solid #d7dee3;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fafb 100%);
  box-shadow: 0 18px 42px rgba(23, 40, 52, 0.12);
  position: relative;
  overflow: hidden;
}

.not-found-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 6px;
  background: linear-gradient(90deg, #0d7f79 0%, #7ac7bc 100%);
}

.not-found-intro {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-group {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  padding: 8px 12px;
  border-radius: 18px;
  background: linear-gradient(180deg, #edf8f5 0%, #e2f3ef 100%);
  border: 1px solid #bcded7;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.status-badge {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0d7f79;
  font-size: 22px;
  box-shadow: none;
  flex-shrink: 0;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #e8f6f3;
  border: 1px solid #bcded7;
  color: #0d6f68;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.not-found-card h1 {
  margin-top: 0;
  color: #183247;
  font-size: 32px;
  line-height: 1.08;
  font-weight: 700;
  max-width: 19ch;
  letter-spacing: -0.03em;
}

.lead {
  margin-top: 16px;
  color: #51606f;
  font-size: 16px;
  line-height: 1.65;
  max-width: 54ch;
}

.route-panel {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f2f6f8;
  border: 1px solid #d7e1e7;
}

.route-label {
  margin-bottom: 8px;
  color: #557081;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.route-panel code {
  display: block;
  overflow-wrap: anywhere;
  color: #0f3148;
  font-size: 15px;
  font-weight: 600;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.actions {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.action-button {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.primary-action {
  border: 1px solid #0d7f79;
  background: #0d7f79;
  color: #ffffff;
}

.primary-action:hover {
  background: #0a706a;
  box-shadow: 0 10px 22px rgba(13, 127, 121, 0.22);
}

.secondary-action {
  border: 1px solid #c9d5dd;
  background: #ffffff;
  color: #26455b;
}

.secondary-action:hover {
  background: #f7fafb;
  border-color: #aebfca;
}

@media (max-width: 900px) {
  .not-found-card {
    padding: 24px 22px;
  }

  .not-found-card h1 {
    font-size: 27px;
    max-width: none;
  }
}

@media (max-width: 600px) {
  .not-found-page {
    padding: 8px;
  }

  .not-found-card {
    padding: 20px 16px;
    border-radius: 14px;
  }

  .not-found-intro {
    gap: 14px;
    align-items: center;
  }

  .status-group {
    gap: 8px;
    padding: 8px 10px;
  }

  .status-badge {
    width: 38px;
    height: 38px;
    font-size: 19px;
  }

  .not-found-card h1 {
    font-size: 24px;
    line-height: 1.12;
  }

  .lead {
    font-size: 14px;
  }

  .actions {
    flex-direction: column;
  }
}
</style>
