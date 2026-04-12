/**
 * Telegram WebApp wrapper
 * Handles init, theme, back button, haptic feedback.
 */
export const tg = {
  init() {
    if (!window.Telegram?.WebApp) return;
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
    this.applyTheme();
  },

  applyTheme() {
    const scheme = window.Telegram?.WebApp?.colorScheme || 'light';
    document.documentElement.setAttribute('data-theme', scheme === 'dark' ? 'dark' : 'light');
  },

  haptic(type = 'light') {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(type);
  },

  close() {
    window.Telegram?.WebApp?.close();
  },

  showAlert(msg) {
    window.Telegram?.WebApp?.showAlert(msg);
  },

  showConfirm(msg, callback) {
    window.Telegram?.WebApp?.showConfirm(msg, callback);
  },
};
