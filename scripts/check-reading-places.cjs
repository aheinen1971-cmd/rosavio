const http = require('node:http');
const assert = require('node:assert/strict');
const select = require('./select-test-content.cjs');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

module.exports = async function checkReadingPlaces(session) {
  const quote = 'Lesestelle für morgen – Grüße aus Köln.';
  let changed = false;
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end('<title>Rosavio Reading Test</title><p style="height:1800px">Test</p><p id="target" style="width:fit-content">' +
      (changed ? 'Inzwischen geänderter Inhalt' : quote) + '</p><p style="height:1000px">Ende</p>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = 'http://127.0.0.1:' + server.address().port + '/article';
  async function until(script, why) {
    let value;
    for (let i = 0; i < 80; i++) {
      value = await session.script(script);
      if (value === true) return;
      await delay(100);
    }
    throw Error(why + ': ' + JSON.stringify(value));
  }
  const chrome = () => session.command('Marionette:SetContext', {value:'chrome'});
  async function nav(uri) {
    await select(session);
    await session.command('WebDriver:Navigate', {url:uri});
  }
  async function click(css) {
    const elem = await session.command('WebDriver:FindElement',{using:'css selector',value:css});
    await session.command('WebDriver:ElementClick',{id:(elem.value || elem)['element-6066-11e4-a52e-4f735466cecf']});
  }
  try {
    await nav(url);
    const point = await session.script(`const el=document.querySelector('#target');el.scrollIntoView({block:'center'});
      const r=document.createRange();r.selectNodeContents(el);getSelection().removeAllRanges();getSelection().addRange(r);
      const b=r.getBoundingClientRect();return {x:Math.round(b.x+b.width/2),y:Math.round(b.y+b.height/2)};`);
    await session.command('WebDriver:PerformActions',{actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},actions:[
      {type:'pointerMove',origin:'viewport',x:point.x,y:point.y},{type:'pointerDown',button:2},{type:'pointerUp',button:2}]}]});
    await chrome();
    await until("const i=document.getElementById('context-rosavio-reading-place');return i && !i.hidden && !i.disabled && !!gContextMenu?.textFragmentURL;", 'Selection command unavailable');
    await click('#context-rosavio-reading-place');
    await until("return gBrowser.selectedBrowser.currentURI.spec==='about:rosavio-notes';",'Notes not opened');
    await select(session);
    await until(`return document.querySelector('#reading-places a')?.textContent.includes(${JSON.stringify(quote)})===true;`,'Quote not saved');
    const link = await session.script("return document.querySelector('#reading-places a').href;");
    assert.ok(link.startsWith(url+'#:~:text='));
    await click('#reading-places a');
    await chrome();
    await until(`return gBrowser.selectedBrowser.currentURI.spec===${JSON.stringify(link)};`,'Reading target not opened');
    await select(session);
    await until("const r=document.querySelector('#target').getBoundingClientRect();return scrollY>0 && r.top>=0 && r.top<innerHeight;", 'Passage not in view');
    changed = true;
    await nav('about:blank');await nav(link);
    assert.equal(await session.script("return document.querySelector('#target').textContent;"),'Inzwischen geänderter Inhalt');
    await nav('about:rosavio-notes');
    await until(`return document.querySelector('#reading-places a')?.textContent.includes(${JSON.stringify(quote)})===true;`,'Excerpt lost when page changed');
    const rosePath=await require('./check-rose-path.cjs')(session,link);
    await click('#reading-places button');await click('#save');
    await until("return !document.getElementById('save').disabled && !Array.from(document.querySelectorAll('#reading-places a')).some(a=>a.textContent.includes('Lesestelle für morgen'));",'Removal not saved');
    await session.command('WebDriver:Refresh');
    await until("return !document.getElementById('save').disabled && !Array.from(document.querySelectorAll('#reading-places a')).some(a=>a.textContent.includes('Lesestelle für morgen'));",'Removal lost');
    return {passed:true,rosePath,contextMenu:true,jumpedToPassage:true,changedPageKeptExcerpt:true,removalPersisted:true};
  } finally {
    await chrome();
    server.closeAllConnections();server.close();
  }
};
