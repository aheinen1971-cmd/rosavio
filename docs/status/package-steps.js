'use strict';
const packageWords={
de:'Paketprüfung|Paket|Version reservieren|Build-Umgebung vorbereiten|Browser bauen|Signatur und lokales Update prüfen|Vorheriges Paket vorbereiten|Öffentliches Update prüfen|Auftragszuordnung prüfen|Flatpak bauen und öffentlich prüfen',
en:'Package checks|Package|Reserve version|Prepare build environment|Build browser|Check signature and local update|Prepare previous package|Test public update|Check job matching|Build and publicly test Flatpak',
fr:'Vérification du paquet|Paquet|Réserver la version|Préparer la compilation|Compiler le navigateur|Vérifier la signature et la mise à jour locale|Préparer le paquet précédent|Tester la mise à jour publique|Vérifier le suivi des tâches|Construire et tester le Flatpak public',
es:'Comprobación del paquete|Paquete|Reservar versión|Preparar la compilación|Compilar el navegador|Verificar firma y actualización local|Preparar paquete anterior|Probar actualización pública|Verificar asignación de tareas|Crear y probar el Flatpak público',
nl:'Pakketcontrole|Pakket|Versie reserveren|Bouwomgeving voorbereiden|Browser bouwen|Handtekening en lokale update controleren|Vorig pakket voorbereiden|Openbare update testen|Taakkoppeling controleren|Flatpak bouwen en openbaar testen',
it:'Verifica del pacchetto|Pacchetto|Riservare la versione|Preparare la compilazione|Compilare il browser|Verificare firma e aggiornamento locale|Preparare il pacchetto precedente|Provare l’aggiornamento pubblico|Verificare le attività associate|Compilare e verificare il Flatpak pubblico',
'pt-PT':'Verificação do pacote|Pacote|Reservar versão|Preparar a compilação|Compilar o navegador|Verificar assinatura e atualização local|Preparar pacote anterior|Testar atualização pública|Verificar associação de tarefas|Compilar e testar o Flatpak público',
pl:'Sprawdzanie pakietu|Pakiet|Zarezerwuj wersję|Przygotuj środowisko kompilacji|Zbuduj przeglądarkę|Sprawdź podpis i lokalną aktualizację|Przygotuj poprzedni pakiet|Sprawdź publiczną aktualizację|Sprawdź powiązanie zadań|Zbuduj i sprawdź publiczny Flatpak',
cs:'Kontrola balíčku|Balíček|Rezervovat verzi|Připravit prostředí|Sestavit prohlížeč|Ověřit podpis a místní aktualizaci|Připravit předchozí balíček|Otestovat veřejnou aktualizaci|Ověřit přiřazení úloh|Sestavit a ověřit veřejný Flatpak',
da:'Pakkekontrol|Pakke|Reservér version|Klargør byggemiljø|Byg browseren|Kontrollér signatur og lokal opdatering|Klargør forrige pakke|Test offentlig opdatering|Kontrollér jobtilknytning|Byg og test den offentlige Flatpak',
'sv-SE':'Paketkontroll|Paket|Reservera version|Förbered byggmiljön|Bygg webbläsaren|Kontrollera signatur och lokal uppdatering|Förbered föregående paket|Testa offentlig uppdatering|Kontrollera jobbkoppling|Bygg och testa offentlig Flatpak',
'nb-NO':'Pakkekontroll|Pakke|Reserver versjon|Klargjør byggemiljøet|Bygg nettleseren|Kontroller signatur og lokal oppdatering|Klargjør forrige pakke|Test offentlig oppdatering|Kontroller jobbtilknytning|Bygg og test offentlig Flatpak',
fi:'Paketin tarkistus|Paketti|Varaa versio|Valmistele käännösympäristö|Käännä selain|Tarkista allekirjoitus ja paikallinen päivitys|Valmistele edellinen paketti|Testaa julkinen päivitys|Tarkista tehtävien kohdistus|Kokoa ja testaa julkinen Flatpak',
tr:'Paket denetimi|Paket|Sürümü ayır|Derleme ortamını hazırla|Tarayıcıyı derle|İmzayı ve yerel güncellemeyi denetle|Önceki paketi hazırla|Herkese açık güncellemeyi test et|Görev eşlemesini denetle|Flatpak paketini derle ve yayımlanan sürümü test et',
uk:'Перевірка пакунка|Пакунок|Зарезервувати версію|Підготувати середовище збирання|Зібрати браузер|Перевірити підпис і локальне оновлення|Підготувати попередній пакунок|Перевірити публічне оновлення|Перевірити зіставлення завдань|Зібрати й перевірити публічний Flatpak',
el:'Έλεγχος πακέτου|Πακέτο|Δέσμευση έκδοσης|Προετοιμασία περιβάλλοντος|Μεταγλώττιση περιηγητή|Έλεγχος υπογραφής και τοπικής ενημέρωσης|Προετοιμασία προηγούμενου πακέτου|Δοκιμή δημόσιας ενημέρωσης|Έλεγχος αντιστοίχισης εργασιών|Δημιουργία και δημόσια δοκιμή του Flatpak',
ja:'パッケージの確認|パッケージ|バージョンを予約|ビルド環境を準備|ブラウザーをビルド|署名とローカル更新を確認|以前のパッケージを準備|公開更新をテスト|ジョブの対応を確認|Flatpak をビルドして公開版をテスト',
ko:'패키지 검사|패키지|버전 예약|빌드 환경 준비|브라우저 빌드|서명 및 로컬 업데이트 확인|이전 패키지 준비|공개 업데이트 테스트|작업 연결 확인|Flatpak 빌드 및 공개 버전 테스트',
ar:'فحص الحزمة|الحزمة|حجز الإصدار|تجهيز بيئة البناء|بناء المتصفح|فحص التوقيع والتحديث المحلي|تجهيز الحزمة السابقة|اختبار التحديث العام|فحص ربط المهام|بناء حزمة Flatpak واختبار الإصدار العام',
he:'בדיקת החבילה|חבילה|שריון גרסה|הכנת סביבת הבנייה|בניית הדפדפן|בדיקת החתימה והעדכון המקומי|הכנת החבילה הקודמת|בדיקת העדכון הציבורי|בדיקת שיוך המשימות|בניית Flatpak ובדיקת הגרסה הציבורית'
};
const packageLabels={Windows:[2,4,5,7],Linux:[2,3,4,5,6,7],Flatpak:[8,9]};
const packageFiles={Windows:'Rosavio-Setup-Deutsch.exe',Linux:'Rosavio-Linux-x64.tar.xz',Flatpak:'io.github.aheinen1971_cmd.Rosavio'};
const phaseIcons={success:'✅',in_progress:'▶',queued:'◷',pending:'◷',waiting:'◷',skipped:'↷',failure:'❌',timed_out:'❌',cancelled:'⊘',unknown:'—'};
function packageBox(row, expanded){
 const states=row.progress?.steps, indices=packageLabels[row.label];
 if(!indices)return null;
 const words=packageWords[statusLanguage].split('|');
 const box=document.createElement('details');box.className='package-box';box.open=expanded;
 const summary=document.createElement('summary');
 const hasSteps=Array.isArray(states)&&states.length===indices.length; const current=hasSteps?states.findIndex(s=>['in_progress','failure','timed_out','cancelled'].includes(s)):-1;
 summary.textContent=words[0]+(current<0?'':' · '+phaseIcons[states[current]]+' '+(current+1)+'/'+indices.length+' · '+words[indices[current]]);
 box.append(summary);
 const file=document.createElement('div');file.textContent=words[1]+' · '+packageFiles[row.label];file.dir='auto';box.append(file);
 if(!hasSteps){const info=document.createElement('small');info.textContent=statusText(row.detail);box.append(info);return box;} const list=document.createElement('ol');
 states.forEach((state,i)=>{const step=document.createElement('li');step.textContent=(phaseIcons[state]||'—')+' '+words[indices[i]];list.append(step);});
 box.append(list);return box;
}
