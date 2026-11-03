/* voice.js - multilingual voice assistant (Web Speech API: works in Chrome / Edge)
   Floating mic button on every page (login page + after login).
   It listens, understands navigation commands in the selected language and speaks back. */
(function () {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const AUTH = document.body.dataset.auth === '1';
  const ROLE = document.body.dataset.role || '';

  // intent -> keywords (lower-case, any language; English always works)
  const INTENTS = {
    dashboard: ['dashboard', 'home page', 'डैशबोर्ड', 'होम', 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'ಡ್ಯಾಶ್ ಬೋರ್ಡ್', 'டாஷ்போர்டு', 'டாஷ் போர்டு', 'డ్యాష్‌బోర్డ్', 'డ్యాష్ బోర్డ్'],
    mock: ['mock', 'test', 'practice', 'मॉक', 'टेस्ट', 'ಮಾಕ್', 'ಟೆಸ್ಟ್', 'மாதிரி', 'தேர்வு', 'మాక్', 'టెస్ట్'],
    interview: ['interview', 'इंटरव्यू', 'साक्षात्कार', 'ಸಂದರ್ಶನ', 'நேர்காணல்', 'ఇంటర్వ్యూ'],
    history: ['history', 'result', 'इतिहास', 'परिणाम', 'ಇತಿಹಾಸ', 'ಫಲಿತಾಂಶ', 'வரலாறு', 'முடிவு', 'చరిత్ర', 'ఫలితం'],
    profile: ['profile', 'resume', 'प्रोफ़ाइल', 'प्रोफाइल', 'रिज़्यूमे', 'रिज्यूमे', 'ಪ್ರೊಫೈಲ್', 'ರೆಸ್ಯೂಮೆ', 'சுயவிவரம்', 'ரெஸ்யூம்', 'ప్రొఫైల్', 'రెజ్యూమె'],
    logout: ['logout', 'log out', 'sign out', 'लॉगआउट', 'लॉग आउट', 'ಲಾಗ್‌ಔಟ್', 'ಲಾಗ್ ಔಟ್', 'வெளியேறு', 'లాగ్ అవుట్', 'లాగ్అవుట్'],
    login: ['login', 'log in', 'sign in', 'लॉगिन', 'लॉग इन', 'ಲಾಗಿನ್', 'உள்நுழை', 'లాగిన్'],
    register: ['register', 'sign up', 'create account', 'रजिस्टर', 'पंजीकरण', 'ನೋಂದಣಿ', 'ನೋಂದಾಯಿಸಿ', 'பதிவு', 'నమోదు'],
    admin: ['admin', 'hr', 'एडमिन', 'ಅಡ್ಮಿನ್', 'நிர்வாக', 'అడ్మిన్'],
  };
  const URLS = { dashboard: '/dashboard', mock: '/mocktest', interview: '/attend', history: '/history',
                 profile: '/profile', logout: '/logout', login: '/login', register: '/register', admin: '/admin' };
  const LANG_WORDS = {
    en: ['english', 'अंग्रेज़ी', 'अंग्रेजी', 'ಇಂಗ್ಲಿಷ್', 'ஆங்கிலம்', 'ఇంగ్లీష్'],
    hi: ['hindi', 'हिन्दी', 'हिंदी', 'ಹಿಂದಿ', 'இந்தி', 'హిందీ'],
    kn: ['kannada', 'कन्नड़', 'ಕನ್ನಡ', 'கன்னடம்', 'కన్నడ'],
    ta: ['tamil', 'तमिल', 'ತಮಿಳು', 'தமிழ்', 'తమిళం'],
    te: ['telugu', 'तेलुगु', 'ತೆಲುಗು', 'தெலுங்கு', 'తెలుగు'],
  };

  const btn = document.createElement('button');
  btn.id = 'voiceBtn'; btn.type = 'button';
  btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
  btn.setAttribute('aria-label', 'Voice assistant');
  const bubble = document.createElement('div');
  bubble.id = 'voiceBubble'; bubble.style.display = 'none';
  document.body.append(btn, bubble);

  function say(text, lang) {
    bubble.textContent = text; bubble.style.display = 'block';
    clearTimeout(say._t); say._t = setTimeout(() => bubble.style.display = 'none', 7000);
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = (I18N.LANGS[lang || getLang()] || I18N.LANGS.en).speech;
    speechSynthesis.speak(u);
  }
  window.voiceSay = say;

  function match(text) {
    text = text.toLowerCase();
    for (const l in LANG_WORDS) {
      if (/(language|भाषा|ಭಾಷೆ|மொழி|భాష)/.test(text) || LANG_WORDS[l].some(w => text.includes(w))) {
        if (LANG_WORDS[l].some(w => text.includes(w))) return { lang: l };
      }
    }
    // check 'logout' before 'login' so "log out" does not match "log"
    for (const k of ['logout', 'interview', 'mock', 'history', 'profile', 'register', 'login', 'admin', 'dashboard']) {
      if (INTENTS[k].some(w => text.includes(w))) return { go: k };
    }
    return null;
  }

  function handle(text) {
    const m = match(text);
    if (!m) return say(t('voice_notheard') + ' ' + t('voice_try'));
    if (m.lang) { setLang(m.lang); return say(t('voice_lang_changed'), m.lang); }
    const k = m.go;
    if (!AUTH && !['login', 'register'].includes(k)) return say(t('voice_login_first'));
    if (AUTH && ['login', 'register'].includes(k)) return say(t('voice_greet_user'));
    if (k === 'admin' && !['admin', 'hr'].includes(ROLE)) return say(t('voice_notheard'));
    say(t('voice_going') + ' ' + text);
    setTimeout(() => location.href = URLS[k], 900);
  }

  let rec = null, listening = false, greeted = false;
  btn.addEventListener('click', () => {
    if (!SR) return say(t('voice_unsupported'));
    if (listening) { rec.stop(); return; }
    if (!greeted) {                       // first click: greet, then listen
      greeted = true;
      say(AUTH ? t('voice_greet_user') : t('voice_greet_guest'));
      setTimeout(start, 4200);
    } else start();
  });

  function start() {
    rec = new SR();
    rec.lang = I18N.LANGS[getLang()].speech;
    rec.interimResults = false; rec.maxAlternatives = 3;
    rec.onstart = () => { listening = true; btn.classList.add('listening'); bubble.textContent = t('voice_listening'); bubble.style.display = 'block'; };
    rec.onend = () => { listening = false; btn.classList.remove('listening'); };
    rec.onerror = () => { listening = false; btn.classList.remove('listening'); say(t('voice_notheard')); };
    rec.onresult = e => {
      const alts = Array.from(e.results[0]).map(a => a.transcript);
      bubble.textContent = '"' + alts[0] + '"';
      handle(alts.join(' | '));
    };
    try { rec.start(); } catch (_) {}
  }
})();
