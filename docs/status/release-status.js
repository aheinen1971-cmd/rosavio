'use strict';
const releaseWords={
 de:'Schon verfügbar|Nächstes Update|Kein neueres Paket angekündigt|Wartet auf den erfolgreichen Linux-Bau. Danach startet Flatpak automatisch.|Linux-Paket veröffentlicht. Der Flatpak-Nachweis steht noch aus.',
 en:'Available now|Next update|No newer package announced|Waiting for the Linux build to pass. Flatpak then starts automatically.|Linux package published. Flatpak verification is pending.',
 fr:'Déjà disponible|Prochaine mise à jour|Aucun paquet plus récent annoncé|En attente de la validation de Linux. Flatpak démarrera ensuite automatiquement.|Paquet Linux publié. La vérification de Flatpak est en attente.',
 es:'Ya disponible|Próxima actualización|No se ha anunciado un paquete más reciente|A la espera de que Linux pase las pruebas. Flatpak se iniciará automáticamente después.|Paquete Linux publicado. Falta verificar Flatpak.',
 nl:'Nu beschikbaar|Volgende update|Geen nieuwer pakket aangekondigd|Wacht tot de Linux-build is goedgekeurd. Daarna start Flatpak automatisch.|Linux-pakket gepubliceerd. Flatpak moet nog worden geverifieerd.',
 it:'Già disponibile|Prossimo aggiornamento|Nessun pacchetto più recente annunciato|In attesa che Linux superi i test. Flatpak partirà automaticamente.|Pacchetto Linux pubblicato. Verifica di Flatpak in attesa.',
 'pt-PT':'Já disponível|Próxima atualização|Nenhum pacote mais recente anunciado|A aguardar a aprovação da compilação Linux. Depois, o Flatpak inicia automaticamente.|Pacote Linux publicado. A verificação do Flatpak está pendente.',
 pl:'Już dostępne|Następna aktualizacja|Nie zapowiedziano nowszego pakietu|Oczekiwanie na pomyślne zakończenie testów Linuksa. Następnie Flatpak uruchomi się automatycznie.|Opublikowano pakiet Linuksa. Weryfikacja Flatpaka w toku lub przed rozpoczęciem.',
 cs:'Již k dispozici|Příští aktualizace|Novější balíček nebyl oznámen|Čeká se na úspěšné sestavení a ověření Linuxu. Poté se Flatpak spustí automaticky.|Balíček pro Linux byl vydán. Ověření Flatpaku zatím není potvrzeno.',
 da:'Tilgængelig nu|Næste opdatering|Ingen nyere pakke annonceret|Afventer godkendt Linux-bygning. Derefter starter Flatpak automatisk.|Linux-pakken er udgivet. Flatpak mangler at blive bekræftet.',
 'sv-SE':'Tillgängligt nu|Nästa uppdatering|Inget nyare paket annonserat|Väntar på godkänd Linux-version. Sedan startar Flatpak automatiskt.|Linux-paketet har publicerats. Flatpak är ännu inte verifierat.',
 'nb-NO':'Tilgjengelig nå|Neste oppdatering|Ingen nyere pakke annonsert|Venter på godkjent Linux-bygg. Deretter starter Flatpak automatisk.|Linux-pakken er publisert. Flatpak er ennå ikke bekreftet.',
 fi:'Nyt saatavilla|Seuraava päivitys|Uudempaa pakettia ei ole ilmoitettu|Odotetaan Linux-koosteen hyväksyntää. Sen jälkeen Flatpak käynnistyy automaattisesti.|Linux-paketti on julkaistu. Flatpakin vahvistus puuttuu vielä.',
 tr:'Şu anda kullanılabilir|Sonraki güncelleme|Daha yeni paket duyurulmadı|Linux derlemesinin testleri geçmesi bekleniyor. Ardından Flatpak otomatik olarak başlar.|Linux paketi yayımlandı. Flatpak henüz doğrulanmadı.',
 uk:'Уже доступно|Наступне оновлення|Новіший пакунок не оголошено|Очікується успішна перевірка Linux. Після цього Flatpak запуститься автоматично.|Пакунок Linux опубліковано. Перевірку Flatpak ще не підтверджено.',
 el:'Ήδη διαθέσιμο|Επόμενη ενημέρωση|Δεν έχει ανακοινωθεί νεότερο πακέτο|Αναμένεται επιτυχής έλεγχος της έκδοσης Linux. Μετά το Flatpak ξεκινά αυτόματα.|Το πακέτο Linux δημοσιεύτηκε. Εκκρεμεί η επαλήθευση του Flatpak.',
 ja:'現在利用可能|次の更新|新しいパッケージの発表はありません|Linux ビルドの検証待ちです。合格後、Flatpak が自動的に開始します。|Linux パッケージは公開済みです。Flatpak の検証結果はまだ確認できません。',
 ko:'현재 사용 가능|다음 업데이트|새 패키지 발표 없음|Linux 빌드가 검사를 통과하면 Flatpak이 자동으로 시작됩니다.|Linux 패키지가 공개되었습니다. Flatpak 검증 결과를 기다리고 있습니다.',
 ar:'متاح الآن|التحديث القادم|لم يُعلَن عن حزمة أحدث|بانتظار نجاح فحص إصدار لينكس. بعد ذلك يبدأ فحص فلاتباك تلقائيًا.|نُشرت حزمة لينكس. لم يتأكد فحص فلاتباك بعد.',
 he:'זמין כעת|העדכון הבא|לא הוכרזה חבילה חדשה יותר|ממתינים לסיום מוצלח של בדיקת לינוקס. לאחר מכן Flatpak יתחיל אוטומטית.|חבילת לינוקס פורסמה. האימות של Flatpak טרם אושר.'
};
function showRelease(cell,row,checkedAt){
 const words=releaseWords[statusLanguage].split('|');
 const add=(label,value)=>{const line=document.createElement('div'),title=document.createElement('strong');title.textContent=label;line.append(title,' · ',value);cell.append(line);};
 const known=row.available;
 const version=known?'🟢 '+known.version+' · #'+known.build:statusText('Prüfung derzeit nicht möglich');
 add(words[0],version);
 const waiting={linux:3,flatpak:4};
 const text=waiting[row.awaiting] ? words[waiting[row.awaiting]] : row.state==='green'?words[2]:statusText(row.detail);
 add(words[1],text);
 const start=Date.parse(row.progress?.startedAt),elapsed=Date.parse(checkedAt)-start;
 if(row.progress?.steps?.includes('in_progress')&&Number.isFinite(elapsed)&&elapsed>=0){
  const stamp=document.createElement('small');stamp.textContent='▶ '+new Intl.RelativeTimeFormat(statusLanguage).format(-Math.floor(elapsed/60000),'minute');cell.append(stamp);
 }
}
