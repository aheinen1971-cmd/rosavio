export class RosavioWorkspaceChild extends JSWindowActorChild {
  async handleEvent(event) {
    if (event.target !== this.document || this.browsingContext.parent ||
        !['about:rosavio-notes','about:rosavio-home'].includes(this.document.documentURI) ||
        !['RosavioWorkspaceRead','RosavioWorkspaceSave'].includes(event.type)) return;
    try {
      const data = await this.sendQuery(event.type === 'RosavioWorkspaceRead'
        ? 'RosavioWorkspace:Read' : 'RosavioWorkspace:Save', event.detail);
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioWorkspaceResult', {
        detail:Cu.cloneInto(data,this.contentWindow)
      }));
    } catch {
      this.document.dispatchEvent(new this.contentWindow.CustomEvent('RosavioWorkspaceError'));
    }
  }
}
