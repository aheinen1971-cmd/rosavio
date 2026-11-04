 'use strict';
var RosavioToolsStrings={};
Services.scriptloader.loadSubScript('chrome://browser/content/rosavio-workspace-l10n.js',RosavioToolsStrings,'UTF-8');
var rosavioToolText=RosavioToolsStrings.RosavioWorkspaceL10n.forLocale(Services.locale.appLocaleAsBCP47).text;

var RosavioTools = {
  async execute(action) {
    const browser=gBrowser.selectedBrowser;
    if(action==='home'||action==='notes'){
      openTrustedLinkIn('about:rosavio-'+action,'tab');return;
    }
    if(action==='reader'){
      if(browser.isArticle||browser.currentURI.spec.startsWith('about:reader?'))
        AboutReaderParent.toggleReaderMode({target:document.documentElement});
      return;
    }
    if(action==='split'){
      if(gBrowser.selectedTab.splitview)BrowserCommands.separateTabSplitView();
      else if(Services.prefs.getBoolPref('browser.tabs.splitView.enabled',false))BrowserCommands.addTabSplitView();
      return;
    }
    if(action==='qr'){
      const url=browser.currentURI.spec;
      if(!/^https?:\/\//i.test(url))return;
      const parsed=new URL(url);if(parsed.username||parsed.password)return;
      const {QRCodeGenerator}=ChromeUtils.importESModule('moz-src:///browser/components/qrcode/QRCodeGenerator.sys.mjs');
      const qrCodeDataURI=await QRCodeGenerator.generateQRCode(url);
      gBrowser.getTabDialogBox(browser).open('chrome://browser/content/qrcode/qrcode-dialog.html',{}, {url,qrCodeDataURI});
    }
  },
  refresh(){
    const view=PanelUI.mainView,browser=gBrowser.selectedBrowser,tab=gBrowser.selectedTab;
    for(const [id,label] of [['qr','Webseite als QR-Code'],['notes','Meine Notizen'],['home','Meine Startseite'],['reader','Lesemodus ein/aus']])view.querySelector('#appMenu-rosavio-'+id).setAttribute('label',rosavioToolText(label));
    view.querySelector('#appMenu-rosavio-reader').disabled=!(browser.isArticle||browser.currentURI.spec.startsWith('about:reader?'));
    view.querySelector('#appMenu-rosavio-qr').disabled=!/^https?:\/\//i.test(browser.currentURI.spec);
    view.querySelector('#appMenu-rosavio-split').disabled=tab.pinned||!Services.prefs.getBoolPref('browser.tabs.splitView.enabled',false);
    view.querySelector('#appMenu-rosavio-split').setAttribute('label',tab.splitview?rosavioToolText("Webseiten wieder trennen"):rosavioToolText("Zwei Webseiten nebeneinander"));
  }
};
document.addEventListener('command',event=>{
 const match=/^appMenu-rosavio-(qr|notes|home|reader|split)$/.exec(event.target.id);
 if(match && PanelUI.mainView.querySelector('#'+event.target.id)===event.target && !event.target.disabled){PanelUI.hide();RosavioTools.execute(match[1]).catch(error=>Cu.reportError(error));}
});
window.addEventListener('load',async()=>{await PanelUI.ensureReady();PanelUI.mainView.addEventListener('ViewShowing',()=>RosavioTools.refresh());},{once:true});

// Use Firefox's selection-specific text fragment, including its disambiguating context.
window.addEventListener('load', () => {
  const menu = document.getElementById('contentAreaContextMenu');
  const native = document.getElementById('context-copy-link-to-highlight');
  if (!menu || !native) return;
  const item = document.createXULElement('menuitem');
  item.id = 'context-rosavio-reading-place';
  item.setAttribute('label', rosavioToolText('Später hier weiterlesen'));
  item.hidden = true;
  native.after(item);
  let selection = null;
  function refresh() {
    item.disabled = !selection || native.disabled || !selection.context.textFragmentURL;
  }
  const observer = new MutationObserver(refresh);
  menu.addEventListener('popupshowing', event => {
    if (event.target !== menu) return;
    const ctx = gContextMenu;
    selection = null;
    if (ctx && !native.hidden && !ctx.inFrame && !ctx.onEditable && !ctx.onTextInput &&
        ctx.isTextSelected && ctx.browser === gBrowser.selectedBrowser &&
        !PrivateBrowsingUtils.isWindowPrivate(window)) {
      const uri = ctx.browser.currentURI;
      if ((uri.schemeIs('https') || uri.schemeIs('http')) && !new URL(uri.spec).username && !new URL(uri.spec).password) {
        selection = {context:ctx, source:uri.spec, quote:ctx.selectionInfo.fullText.trim()};
      }
    }
    item.hidden = !selection;
    refresh();
    observer.observe(native,{attributes:true,attributeFilter:['disabled']});
  });
  menu.addEventListener('popuphidden', event => {
    if (event.target === menu) observer.disconnect();
  });
  item.addEventListener('command', async event => {
    if (!event.isTrusted || item.hidden || item.disabled || !selection) return;
    const {context, source, quote} = selection;
    try {
      if (context.browser !== gBrowser.selectedBrowser || context.browser.currentURI.spec !== source) return;
      const target = new URL(context.textFragmentURL);
      const original = new URL(source);
      if (target.href.split('#')[0] !== original.href.split('#')[0]) return;
      const {RosavioWorkspaceParent} = ChromeUtils.importESModule('resource:///actors/RosavioWorkspaceParent.sys.mjs');
      const excerpt = quote.slice(0,1000).replace(/[\uD800-\uDBFF]$/, '');
      await RosavioWorkspaceParent.addPlace(window,{url:target.href,quote:excerpt+(excerpt.length<quote.length?'…':'')});
      openTrustedLinkIn('about:rosavio-notes','tab');
    } catch (error) {
      Cu.reportError(error);
      Services.prompt.alert(window,'Rosavio',rosavioToolText('Lesestelle konnte nicht gespeichert werden (höchstens 30).'));
    }
  });
},{once:true});

