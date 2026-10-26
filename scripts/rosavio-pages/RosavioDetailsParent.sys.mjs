// The content page receives only this fixed, read-only summary. No preference
// names, URLs, profile paths, or write operations are accepted from content.
import { AppConstants } from 'resource://gre/modules/AppConstants.sys.mjs';
export class RosavioDetailsParent extends JSWindowActorParent {
  receiveMessage(message) {
    const uri = this.manager.documentURI?.spec;
    if (message.name !== 'Rosavio:Summary' ||
        !['about:rosavio-privacy', 'about:rosavio-updates'].includes(uri) ||
        this.browsingContext.parent) {
      throw new Error('Rosavio summary request denied');
    }
    const bool = name => Services.prefs.getBoolPref(name, false);
    const text = name => Services.prefs.getStringPref(name, '');
    return {
      version: Services.appinfo.version,
      buildID: Services.appinfo.appBuildID,
      locale: Services.locale.appLocaleAsBCP47,
      trackingCategory: text('browser.contentblocking.category'),
      tracking: bool('privacy.trackingprotection.enabled'),
      trackingPrivate: bool('privacy.trackingprotection.pbmode.enabled'),
      cookies: Services.prefs.getIntPref('network.cookie.cookieBehavior', -1),
      malware: bool('browser.safebrowsing.malware.enabled'),
      phishing: bool('browser.safebrowsing.phishing.enabled'),
      downloads: bool('browser.safebrowsing.downloads.enabled'),
      unwanted: bool('browser.safebrowsing.downloads.remote.block_potentially_unwanted'),
      uncommon: bool('browser.safebrowsing.downloads.remote.block_uncommon'),
      telemetry: !!AppConstants.MOZ_TELEMETRY_REPORTING &&
        bool('datareporting.policy.dataSubmissionEnabled') &&
        bool('datareporting.healthreport.uploadEnabled'),
      settingsRedesign: bool('browser.settings-redesign.enabled'),
      sponsored: bool('browser.newtabpage.activity-stream.showSponsored') ||
        bool('browser.newtabpage.activity-stream.showSponsoredTopSites'),
      updateAllowed: Services.policies.isAllowed('appUpdate'),
    };
  }
}
