export class RosavioDetailsChild extends JSWindowActorChild {
  async handleEvent(event) {
    if (event.target !== this.document || this.browsingContext.parent ||
        !['about:rosavio-privacy', 'about:rosavio-updates'].includes(this.document.documentURI)) {
      return;
    }
    try {
      if (event.type === 'RosavioOpenPageRequest') {
        const names = {privacy:'Rosavio:OpenPrivacy', security:'Rosavio:OpenSecurity', addons:'Rosavio:OpenAddons'};
        if (Object.hasOwn(names, event.detail)) await this.sendQuery(names[event.detail]);
        return;
      }
      const summary = await this.sendQuery('Rosavio:Summary');
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioSummary', {
        detail: Cu.cloneInto(summary, this.contentWindow),
      }));
    } catch (error) {
      Cu.reportError(new Error('Rosavio information page request failed: ' + String(error)));
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioSummaryError'));
    }
  }
}
