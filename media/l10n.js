/* Extension pages only: page scanning stays self-contained and unprivileged. */
function mediaText(key, values = {}) {
  const message = browser.i18n.getMessage(key);
  if (!message) throw new Error('Missing media translation: ' + key);
  return message.replace(/\{([a-z]+)\}/g, (token, name) =>
    Object.hasOwn(values, name) ? String(values[name]) : token);
}
const mediaLocale = browser.i18n.getUILanguage();
function mediaNumber(value, options) {
  return new Intl.NumberFormat(mediaLocale, options).format(value);
}
function mediaError(key, values) {
  const error = new Error(mediaText(key, values));
  error.mediaLocalized = true;
  return error;
}
function mediaErrorText(error) {
  // Third-party and platform exception text is not under our translation control.
  return error?.mediaLocalized ? error.message : mediaText('unexpected');
}
function localizeMediaPage(root = document) {
  if (root === document) {
    document.documentElement.lang = mediaLocale;
    document.documentElement.dir = /^(ar|he)(-|$)/i.test(mediaLocale) ? 'rtl' : 'ltr';
  }
  for (const element of root.querySelectorAll('[data-i18n]')) {
    element.textContent = mediaText(element.dataset.i18n);
  }
  for (const element of root.querySelectorAll('[data-i18n-label]')) {
    element.setAttribute('aria-label', mediaText(element.dataset.i18nLabel));
  }
  for (const template of root.querySelectorAll('template')) localizeMediaPage(template.content);
}
localizeMediaPage();
