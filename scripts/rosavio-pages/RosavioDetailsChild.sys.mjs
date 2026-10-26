export class RosavioDetailsChild extends JSWindowActorChild {
  async handleEvent(event) {
    if (event.target !== this.document || this.browsingContext.parent ||
        !['about:rosavio-privacy', 'about:rosavio-updates'].includes(this.document.documentURI)) {
      return;
    }
    try {
      const summary = await this.sendQuery('Rosavio:Summary');
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioSummary', {
        detail: Cu.cloneInto(summary, this.contentWindow),
      }));
    } catch {
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioSummaryError'));
    }
  }
}
