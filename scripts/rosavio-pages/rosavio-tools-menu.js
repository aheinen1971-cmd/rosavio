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
