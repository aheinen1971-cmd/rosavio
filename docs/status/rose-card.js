'use strict';
const cardWords={
 de:'Kann ich den Rosenpfad schon nutzen?|Letzte Änderung|Jetzt herunterladen|Noch nicht bestätigt',
 en:'Can I use Rose Path yet?|Last change|Download now|Not yet confirmed',
 fr:'Puis-je déjà utiliser le chemin des roses ?|Dernier changement|Télécharger|Pas encore confirmé',
 es:'¿Ya puedo usar el camino de rosas?|Último cambio|Descargar ahora|Aún sin confirmar',
 nl:'Kan ik het rozenpad al gebruiken?|Laatste wijziging|Nu downloaden|Nog niet bevestigd',
 it:'Posso già usare il percorso delle rose?|Ultima modifica|Scarica ora|Non ancora confermato',
 'pt-PT':'Já posso usar o caminho das rosas?|Última alteração|Transferir agora|Ainda por confirmar',
 pl:'Czy mogę już używać różanej ścieżki?|Ostatnia zmiana|Pobierz teraz|Jeszcze nie potwierdzono',
 cs:'Mohu už používat růžovou cestu?|Poslední změna|Stáhnout|Zatím nepotvrzeno',
 da:'Kan jeg bruge rosenstien nu?|Seneste ændring|Hent nu|Endnu ikke bekræftet',
 'sv-SE':'Kan jag använda rosenstigen nu?|Senaste ändring|Ladda ner nu|Ännu inte bekräftat',
 'nb-NO':'Kan jeg bruke rosestien nå?|Siste endring|Last ned nå|Ennå ikke bekreftet',
 fi:'Voinko jo käyttää ruusupolkua?|Viimeisin muutos|Lataa nyt|Ei vielä vahvistettu',
 tr:'Gül yolunu kullanabilir miyim?|Son değişiklik|Şimdi indir|Henüz doğrulanmadı',
 uk:'Чи вже можна користуватися трояндовою стежкою?|Остання зміна|Завантажити|Ще не підтверджено',
 el:'Μπορώ ήδη να χρησιμοποιήσω το μονοπάτι των ρόδων;|Τελευταία αλλαγή|Λήψη τώρα|Δεν έχει επιβεβαιωθεί ακόμη',
 ja:'ローズパスはもう使えますか？|最終変更|ダウンロード|まだ確認されていません',
 ko:'장미길을 벌써 사용할 수 있나요?|최근 변경|지금 다운로드|아직 확인되지 않음',
 ar:'هل يمكنني استخدام مسار الورود الآن؟|آخر تغيير|تنزيل الآن|لم يتأكد بعد',
 he:'האם כבר אפשר להשתמש בשביל הוורדים?|השינוי האחרון|להורדה|טרם אושר'
};
const roseNames={"de": ["Rosenpfad", "Später hier weiterlesen"], "en": ["Rose Trail", "Continue reading here later"], "fr": ["Parcours des roses", "Reprendre la lecture ici plus tard"], "es": ["Ruta de rosas", "Seguir leyendo aquí más tarde"], "nl": ["Rozenpad", "Later hier verder lezen"], "it": ["Sentiero delle rose", "Riprendi la lettura da qui più tardi"], "pt-PT": ["Caminho das rosas", "Continuar a ler aqui mais tarde"], "pl": ["Różana ścieżka", "Wróć później do tego fragmentu"], "cs": ["Růžová stezka", "Pokračovat zde ve čtení později"], "da": ["Rosenstien", "Læs videre her senere"], "sv-SE": ["Rosenstigen", "Läs vidare här senare"], "nb-NO": ["Rosenstien", "Les videre her senere"], "fi": ["Ruusupolku", "Jatka lukemista tästä myöhemmin"], "tr": ["Gül Yolu", "Daha sonra buradan okumaya devam et"], "uk": ["Трояндова стежка", "Продовжити читати звідси пізніше"], "el": ["Μονοπάτι των ρόδων", "Συνέχεια ανάγνωσης από εδώ αργότερα"], "ja": ["バラの小道", "後でここから読み続ける"], "ko": ["장미길", "나중에 여기서 이어 읽기"], "ar": ["درب الورد", "متابعة القراءة من هنا لاحقًا"], "he": ["שביל הוורדים", "להמשיך לקרוא מכאן מאוחר יותר"]};
const roseDescription={"de": "Füge gespeicherte Lesestellen zum Pfad hinzu. Speichere deine Reihenfolge und Notizen. Änderungen werden erst mit „Speichern“ dauerhaft gesichert.", "en": "Add saved passages to your trail. Save their order and your notes. Changes are only saved permanently when you click “Save”.", "fr": "Ajoutez des passages enregistrés au parcours. Enregistrez leur ordre et vos notes. Les modifications ne sont enregistrées définitivement que lorsque vous cliquez sur « Enregistrer ».", "es": "Añade pasajes guardados a la ruta. Guarda su orden y tus notas. Los cambios solo se guardan permanentemente cuando haces clic en \"Guardar\".", "nl": "Voeg bewaarde leesplekken toe aan het pad. Sla de volgorde en je notities op. Wijzigingen worden pas definitief opgeslagen als u op “Opslaan” klikt.", "it": "Aggiungi i brani salvati al sentiero. Salva il loro ordine e le tue note. Le modifiche vengono salvate in modo permanente solo quando si fa clic su \"Salva\".", "pt-PT": "Adiciona passagens guardadas ao caminho. Guarda a ordem e as tuas notas. As alterações só são salvas permanentemente quando você clica em “Salvar”.", "pl": "Dodaj zapisane fragmenty do ścieżki. Zapisz ich kolejność i swoje notatki. Zmiany zostaną trwale zapisane dopiero po kliknięciu „Zapisz”.", "cs": "Přidejte na stezku uložené pasáže. Uložte jejich pořadí a své poznámky. Změny se trvale uloží pouze po kliknutí na „Uložit“.", "da": "Føj gemte læsesteder til stien. Gem rækkefølgen og dine noter. Ændringer gemmes kun permanent, når du klikker på \"Gem\".", "sv-SE": "Lägg till sparade läsställen på stigen. Spara ordningen och dina anteckningar. Ändringar sparas bara permanent när du klickar på \"Spara\".", "nb-NO": "Legg til lagrede lesesteder på stien. Lagre rekkefølgen og notatene dine. Endringer lagres bare permanent når du klikker \"Lagre\".", "fi": "Lisää tallennettuja lukukohtia polulle. Tallenna järjestys ja muistiinpanosi. Muutokset tallennetaan pysyvästi vain, kun napsautat \"Tallenna\".", "tr": "Kaydedilen okuma yerlerini yola ekleyin. Sıralamayı ve notlarınızı kaydedin. Değişiklikler yalnızca “Kaydet”e tıkladığınızda kalıcı olarak kaydedilir.", "uk": "Додайте збережені уривки до стежки. Збережіть їх порядок і свої нотатки. Зміни зберігаються остаточно лише після натискання кнопки «Зберегти».", "el": "Προσθέστε αποθηκευμένα αποσπάσματα στο μονοπάτι. Αποθηκεύστε τη σειρά τους και τις σημειώσεις σας. Οι αλλαγές αποθηκεύονται μόνιμα μόνο όταν κάνετε κλικ στο \"Αποθήκευση\".", "ja": "保存した読書位置を小道に追加します。順序とメモを保存してください。 変更は「保存」をクリックした場合にのみ永続的に保存されます。", "ko": "저장한 읽기 위치를 장미길에 추가하세요. 순서와 메모를 저장하세요. 변경 사항은 \"저장\"을 클릭한 경우에만 영구적으로 저장됩니다.", "ar": "أضف مواضع القراءة المحفوظة إلى الدرب، ثم احفظ ترتيبها وملاحظاتك. يتم حفظ التغييرات بشكل دائم فقط عند النقر فوق \"حفظ\".", "he": "אפשר להוסיף לשביל קטעים ששמרת ולשמור את הסדר ואת ההערות שלך. השינויים נשמרים לצמיתות רק כאשר אתה לוחץ על \"שמור\"."};
let rosePlatform='Windows';
function roseCard(data){
 const card=document.getElementById('rose-card'),names=roseNames[statusLanguage],words=cardWords[statusLanguage].split('|');
 if(!card.childElementCount){
  const title=document.createElement('h2');title.textContent='🌹 '+words[0];card.append(title);
  const intro=document.createElement('p');intro.textContent=roseDescription[statusLanguage];card.append(intro);
  const group=document.createElement('div');group.className='rose-choices';
  for(const platform of Object.keys(packageLabels)){
   const button=document.createElement('button');button.type='button';button.textContent=platform;
   button.onclick=()=>{rosePlatform=platform;roseCard(last||data);};group.append(button);
  }
  const body=document.createElement('div');body.className='rose-body';body.setAttribute('aria-live','polite');card.append(group,body);
 }
 for(const button of card.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.textContent===rosePlatform));
 const row=data.rows.find(r=>r.label===rosePlatform);if(!row)return;
 const lines=document.createDocumentFragment(),wordsRelease=releaseWords[statusLanguage].split('|');
 const line=(label,text)=>{const p=document.createElement('p'),b=document.createElement('strong');b.textContent=label;p.append(b,' · ',text);lines.append(p);};
 const ready=row.features?.rose===true;
 line(wordsRelease[0],row.features?.reading||ready?'🟢 '+(ready?names[0]:names[1]):row.available?'🟢 '+row.available.version:words[3]);
 const active=row.progress?.steps?.indexOf('in_progress')??-1;
 const phase=active>=0?packageWords[statusLanguage].split('|')[packageLabels[rosePlatform][active]]:null;
 const state=row.awaiting==='linux'?wordsRelease[3]:row.awaiting==='flatpak'?wordsRelease[4]:phase||statusText(row.detail);
 if(!ready)line(names[0],(row.state==='yellow'?'🟡 ':row.state==='red'?'🔴 ':'⚪ ')+(row.state==='green'?words[3]:state));
 if(ready&&row.features.download){
  const url=new URL(row.features.download);
  if(url.protocol==='https:'&&['github.com','aheinen1971-cmd.github.io'].includes(url.hostname)){
   const a=document.createElement('a');a.href=url.href;a.textContent=words[2]+' · '+rosePlatform;lines.append(a);
  }
 }
 const when=Date.parse(row.roseChange?.at);
 if(Number.isFinite(when)){
  const date=new Intl.DateTimeFormat(statusLanguage,{dateStyle:'short',timeStyle:'short',timeZone:'Europe/Berlin'}).format(when);
  const linux=data.rows.find(r=>r.label==='Linux'),idx=linux?.progress?.steps?.indexOf('in_progress')??-1;
  const event=row.awaiting==='linux'&&idx>=0?'Linux · '+packageWords[statusLanguage].split('|')[packageLabels.Linux[idx]]:state;
  line(words[1],date+' · '+event);
 }else line(words[1],'—');
 card.querySelector('.rose-body').replaceChildren(lines);card.hidden=false;
}
