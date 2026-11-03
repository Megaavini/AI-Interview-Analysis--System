/* i18n.js - client-side multi-language support (English, Hindi, Kannada, Tamil, Telugu)
   Usage in HTML:  <span data-i18n="key">English text</span>
                   <input data-i18n-ph="key">   (placeholder)
   In JS:          t('key')  ,  getLang()  ,  setLang('hi')                                   */
(function () {
  const LANGS = {
    en: { name: 'English', speech: 'en-IN' },
    hi: { name: 'हिन्दी', speech: 'hi-IN' },
    kn: { name: 'ಕನ್ನಡ', speech: 'kn-IN' },
    ta: { name: 'தமிழ்', speech: 'ta-IN' },
    te: { name: 'తెలుగు', speech: 'te-IN' },
  };

  const D = {
    en: {
      nav_dashboard: 'Dashboard', nav_mock: 'Mock Test', nav_interview: 'Attend Interview', nav_history: 'History',
      nav_profile: 'Profile', nav_admin: 'Admin / HR', nav_logout: 'Logout', nav_login: 'Login', nav_register: 'Register',
      voice_title: 'Voice assistant', voice_listening: 'Listening...', voice_try: 'Try: "dashboard", "mock test", "interview", "history", "logout"',
      voice_unsupported: 'Voice recognition is not supported in this browser. Please use Chrome or Edge.',
      voice_notheard: 'Sorry, I did not catch that. Please try again.', voice_login_first: 'Please login first.',
      voice_greet_guest: 'Hello! I am your interview assistant. You can say login, register, or change language.',
      voice_greet_user: 'Hello! You can say dashboard, mock test, interview, history, profile or logout.',
      voice_going: 'Opening', voice_lang_changed: 'Language changed to English.',
      login_title: 'Welcome Back', username: 'Username', password: 'Password', login_btn: 'Login',
      no_account: "Don't have an account?", have_account: 'Already have an account?',
      register_title: 'Create Account', full_name: 'Full name', email: 'E-mail', phone: 'Phone (optional)',
      resume_opt: 'Resume (PDF / DOC / DOCX, optional)', register_btn: 'Register',
      dash_title: 'Dashboard', mock_title: 'Mock Test', mock_desc: 'Practice with difficulty-based multiple-choice questions',
      start_mock: 'Start Mock Test', int_title: 'Attend Interview', int_desc: 'Live AI-proctored interview with emotion detection',
      go_interview: 'Go to Interview', view_results: 'View all results', my_resume: 'My Resume', upload_resume: 'Upload resume',
      update_profile: 'Update profile', no_resume: 'No resume uploaded yet', shortlisted_banner: 'You have been shortlisted!',
      messages: 'Messages from HR', recent_interviews: 'Recent interview results',
      att_title: 'AI Interview', att_sub: 'Camera-monitored interview with emotion analysis and anti-spoofing',
      choose_subject: 'Choose your subject', start_interview: 'Start Interview', camera_note: 'Your camera must be on during the interview. Frames are analysed for emotion and liveness.',
      question: 'Question', your_answer: 'Your answer', type_or_speak: 'Type your answer or use the microphone...',
      speak_answer: 'Speak answer', stop: 'Stop', read_q: 'Read question', next_q: 'Next question', finish: 'Submit interview',
      live_check: 'Liveness', emotion: 'Emotion', camera_on: 'Camera on', camera_off: 'Camera is off - allow camera access',
      feedback_title: 'Interview Feedback', feedback_sub: 'Tell us about your experience', rating: 'Rating',
      comments: 'Comments', submit_feedback: 'Submit & see result',
      report_card: 'Interview Report Card', interview_marks: 'Interview marks', personality_marks: 'Personality marks',
      overall: 'Overall score', grade: 'Grade', mock_avg: 'Mock test average', strengths: 'Strengths', improvements: 'Areas to improve',
      q_review: 'Question-wise correction', model_answer: 'Explanation', your_ans: 'Your answer', emotion_profile: 'Emotion profile',
      integrity: 'Integrity report', print: 'Print / Save PDF', back_dashboard: 'Back to dashboard',
      language: 'Language',
    },
    hi: {
      nav_dashboard: 'डैशबोर्ड', nav_mock: 'मॉक टेस्ट', nav_interview: 'इंटरव्यू दें', nav_history: 'इतिहास',
      nav_profile: 'प्रोफ़ाइल', nav_admin: 'एडमिन / एचआर', nav_logout: 'लॉगआउट', nav_login: 'लॉगिन', nav_register: 'रजिस्टर',
      voice_title: 'वॉइस असिस्टेंट', voice_listening: 'सुन रहा हूँ...', voice_try: 'बोलें: "डैशबोर्ड", "मॉक टेस्ट", "इंटरव्यू", "इतिहास", "लॉगआउट"',
      voice_unsupported: 'इस ब्राउज़र में वॉइस सपोर्ट नहीं है। कृपया Chrome या Edge इस्तेमाल करें।',
      voice_notheard: 'माफ़ कीजिए, मैं समझ नहीं पाया। कृपया फिर से बोलें।', voice_login_first: 'कृपया पहले लॉगिन करें।',
      voice_greet_guest: 'नमस्ते! मैं आपका इंटरव्यू असिस्टेंट हूँ। आप लॉगिन, रजिस्टर या भाषा बदलें बोल सकते हैं।',
      voice_greet_user: 'नमस्ते! आप डैशबोर्ड, मॉक टेस्ट, इंटरव्यू, इतिहास, प्रोफ़ाइल या लॉगआउट बोल सकते हैं।',
      voice_going: 'खोल रहा हूँ', voice_lang_changed: 'भाषा हिन्दी में बदल दी गई है।',
      login_title: 'वापसी पर स्वागत है', username: 'यूज़रनेम', password: 'पासवर्ड', login_btn: 'लॉगिन',
      no_account: 'खाता नहीं है?', have_account: 'पहले से खाता है?',
      register_title: 'खाता बनाएँ', full_name: 'पूरा नाम', email: 'ई-मेल', phone: 'फ़ोन (वैकल्पिक)',
      resume_opt: 'रिज़्यूमे (PDF / DOC / DOCX, वैकल्पिक)', register_btn: 'रजिस्टर करें',
      dash_title: 'डैशबोर्ड', mock_title: 'मॉक टेस्ट', mock_desc: 'कठिनाई स्तर वाले बहुविकल्पीय प्रश्नों का अभ्यास करें',
      start_mock: 'मॉक टेस्ट शुरू करें', int_title: 'इंटरव्यू दें', int_desc: 'भावना पहचान के साथ लाइव AI-निगरानी वाला इंटरव्यू',
      go_interview: 'इंटरव्यू पर जाएँ', view_results: 'सभी परिणाम देखें', my_resume: 'मेरा रिज़्यूमे', upload_resume: 'रिज़्यूमे अपलोड करें',
      update_profile: 'प्रोफ़ाइल अपडेट करें', no_resume: 'अभी तक रिज़्यूमे अपलोड नहीं हुआ', shortlisted_banner: 'आपको शॉर्टलिस्ट किया गया है!',
      messages: 'एचआर के संदेश', recent_interviews: 'हाल के इंटरव्यू परिणाम',
      att_title: 'AI इंटरव्यू', att_sub: 'भावना विश्लेषण और स्पूफ़िंग-जाँच के साथ कैमरा-निगरानी इंटरव्यू',
      choose_subject: 'अपना विषय चुनें', start_interview: 'इंटरव्यू शुरू करें', camera_note: 'इंटरव्यू के दौरान कैमरा चालू रहना चाहिए। फ़्रेम का भावना और लाइवनेस के लिए विश्लेषण होता है।',
      question: 'प्रश्न', your_answer: 'आपका उत्तर', type_or_speak: 'अपना उत्तर लिखें या माइक्रोफ़ोन का उपयोग करें...',
      speak_answer: 'बोलकर उत्तर दें', stop: 'रोकें', read_q: 'प्रश्न सुनें', next_q: 'अगला प्रश्न', finish: 'इंटरव्यू समाप्त करें',
      live_check: 'लाइवनेस', emotion: 'भावना', camera_on: 'कैमरा चालू', camera_off: 'कैमरा बंद है - कैमरा अनुमति दें',
      feedback_title: 'इंटरव्यू फ़ीडबैक', feedback_sub: 'अपना अनुभव बताएँ', rating: 'रेटिंग',
      comments: 'टिप्पणियाँ', submit_feedback: 'जमा करें और परिणाम देखें',
      report_card: 'इंटरव्यू रिपोर्ट कार्ड', interview_marks: 'इंटरव्यू अंक', personality_marks: 'व्यक्तित्व अंक',
      overall: 'कुल स्कोर', grade: 'ग्रेड', mock_avg: 'मॉक टेस्ट औसत', strengths: 'ताकत', improvements: 'सुधार के क्षेत्र',
      q_review: 'प्रश्न-वार सुधार', model_answer: 'आदर्श उत्तर', your_ans: 'आपका उत्तर', emotion_profile: 'भावना प्रोफ़ाइल',
      integrity: 'अखंडता रिपोर्ट', print: 'प्रिंट / PDF सहेजें', back_dashboard: 'डैशबोर्ड पर वापस',
      language: 'भाषा',
    },
    kn: {
      nav_dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', nav_mock: 'ಮಾಕ್ ಟೆಸ್ಟ್', nav_interview: 'ಸಂದರ್ಶನ ಬರೆಯಿರಿ', nav_history: 'ಇತಿಹಾಸ',
      nav_profile: 'ಪ್ರೊಫೈಲ್', nav_admin: 'ಅಡ್ಮಿನ್ / ಎಚ್‌ಆರ್', nav_logout: 'ಲಾಗ್‌ಔಟ್', nav_login: 'ಲಾಗಿನ್', nav_register: 'ನೋಂದಣಿ',
      voice_title: 'ಧ್ವನಿ ಸಹಾಯಕ', voice_listening: 'ಆಲಿಸುತ್ತಿದ್ದೇನೆ...', voice_try: 'ಹೇಳಿ: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "ಮಾಕ್ ಟೆಸ್ಟ್", "ಸಂದರ್ಶನ", "ಇತಿಹಾಸ", "ಲಾಗ್‌ಔಟ್"',
      voice_unsupported: 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಬೆಂಬಲ ಇಲ್ಲ. ದಯವಿಟ್ಟು Chrome ಅಥವಾ Edge ಬಳಸಿ.',
      voice_notheard: 'ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಿ.', voice_login_first: 'ದಯವಿಟ್ಟು ಮೊದಲು ಲಾಗಿನ್ ಮಾಡಿ.',
      voice_greet_guest: 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸಂದರ್ಶನ ಸಹಾಯಕ. ಲಾಗಿನ್, ನೋಂದಣಿ ಅಥವಾ ಭಾಷೆ ಬದಲಿಸಿ ಎಂದು ಹೇಳಬಹುದು.',
      voice_greet_user: 'ನಮಸ್ಕಾರ! ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಮಾಕ್ ಟೆಸ್ಟ್, ಸಂದರ್ಶನ, ಇತಿಹಾಸ, ಪ್ರೊಫೈಲ್ ಅಥವಾ ಲಾಗ್‌ಔಟ್ ಎಂದು ಹೇಳಬಹುದು.',
      voice_going: 'ತೆರೆಯುತ್ತಿದ್ದೇನೆ', voice_lang_changed: 'ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಿಸಲಾಗಿದೆ.',
      login_title: 'ಮರಳಿ ಸ್ವಾಗತ', username: 'ಬಳಕೆದಾರ ಹೆಸರು', password: 'ಪಾಸ್‌ವರ್ಡ್', login_btn: 'ಲಾಗಿನ್',
      no_account: 'ಖಾತೆ ಇಲ್ಲವೇ?', have_account: 'ಈಗಾಗಲೇ ಖಾತೆ ಇದೆಯೇ?',
      register_title: 'ಖಾತೆ ರಚಿಸಿ', full_name: 'ಪೂರ್ಣ ಹೆಸರು', email: 'ಇ-ಮೇಲ್', phone: 'ಫೋನ್ (ಐಚ್ಛಿಕ)',
      resume_opt: 'ರೆಸ್ಯೂಮೆ (PDF / DOC / DOCX, ಐಚ್ಛಿಕ)', register_btn: 'ನೋಂದಾಯಿಸಿ',
      dash_title: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', mock_title: 'ಮಾಕ್ ಟೆಸ್ಟ್', mock_desc: 'ಕಠಿಣತೆಯ ಹಂತಗಳ ಬಹು-ಆಯ್ಕೆ ಪ್ರಶ್ನೆಗಳ ಅಭ್ಯಾಸ',
      start_mock: 'ಮಾಕ್ ಟೆಸ್ಟ್ ಪ್ರಾರಂಭಿಸಿ', int_title: 'ಸಂದರ್ಶನ ಬರೆಯಿರಿ', int_desc: 'ಭಾವನೆ ಪತ್ತೆಯೊಂದಿಗೆ ಲೈವ್ AI ಮೇಲ್ವಿಚಾರಣೆಯ ಸಂದರ್ಶನ',
      go_interview: 'ಸಂದರ್ಶನಕ್ಕೆ ಹೋಗಿ', view_results: 'ಎಲ್ಲಾ ಫಲಿತಾಂಶ ನೋಡಿ', my_resume: 'ನನ್ನ ರೆಸ್ಯೂಮೆ', upload_resume: 'ರೆಸ್ಯೂಮೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
      update_profile: 'ಪ್ರೊಫೈಲ್ ನವೀಕರಿಸಿ', no_resume: 'ಇನ್ನೂ ರೆಸ್ಯೂಮೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿಲ್ಲ', shortlisted_banner: 'ನಿಮ್ಮನ್ನು ಶಾರ್ಟ್‌ಲಿಸ್ಟ್ ಮಾಡಲಾಗಿದೆ!',
      messages: 'ಎಚ್‌ಆರ್ ಸಂದೇಶಗಳು', recent_interviews: 'ಇತ್ತೀಚಿನ ಸಂದರ್ಶನ ಫಲಿತಾಂಶಗಳು',
      att_title: 'AI ಸಂದರ್ಶನ', att_sub: 'ಭಾವನೆ ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ನಕಲಿ-ಮುಖ ಪತ್ತೆಯೊಂದಿಗೆ ಕ್ಯಾಮೆರಾ ಸಂದರ್ಶನ',
      choose_subject: 'ನಿಮ್ಮ ವಿಷಯ ಆಯ್ಕೆಮಾಡಿ', start_interview: 'ಸಂದರ್ಶನ ಪ್ರಾರಂಭಿಸಿ', camera_note: 'ಸಂದರ್ಶನದ ಸಮಯದಲ್ಲಿ ಕ್ಯಾಮೆರಾ ಆನ್ ಆಗಿರಬೇಕು. ಭಾವನೆ ಮತ್ತು ಲೈವ್‌ನೆಸ್‌ಗಾಗಿ ಫ್ರೇಮ್‌ಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತದೆ.',
      question: 'ಪ್ರಶ್ನೆ', your_answer: 'ನಿಮ್ಮ ಉತ್ತರ', type_or_speak: 'ನಿಮ್ಮ ಉತ್ತರ ಬರೆಯಿರಿ ಅಥವಾ ಮೈಕ್ ಬಳಸಿ...',
      speak_answer: 'ಮಾತನಾಡಿ ಉತ್ತರಿಸಿ', stop: 'ನಿಲ್ಲಿಸಿ', read_q: 'ಪ್ರಶ್ನೆ ಓದಿ', next_q: 'ಮುಂದಿನ ಪ್ರಶ್ನೆ', finish: 'ಸಂದರ್ಶನ ಮುಗಿಸಿ',
      live_check: 'ಲೈವ್‌ನೆಸ್', emotion: 'ಭಾವನೆ', camera_on: 'ಕ್ಯಾಮೆರಾ ಆನ್', camera_off: 'ಕ್ಯಾಮೆರಾ ಆಫ್ ಇದೆ - ಅನುಮತಿ ನೀಡಿ',
      feedback_title: 'ಸಂದರ್ಶನ ಪ್ರತಿಕ್ರಿಯೆ', feedback_sub: 'ನಿಮ್ಮ ಅನುಭವ ತಿಳಿಸಿ', rating: 'ರೇಟಿಂಗ್',
      comments: 'ಅಭಿಪ್ರಾಯಗಳು', submit_feedback: 'ಸಲ್ಲಿಸಿ ಮತ್ತು ಫಲಿತಾಂಶ ನೋಡಿ',
      report_card: 'ಸಂದರ್ಶನ ವರದಿ ಕಾರ್ಡ್', interview_marks: 'ಸಂದರ್ಶನ ಅಂಕಗಳು', personality_marks: 'ವ್ಯಕ್ತಿತ್ವ ಅಂಕಗಳು',
      overall: 'ಒಟ್ಟು ಅಂಕ', grade: 'ಗ್ರೇಡ್', mock_avg: 'ಮಾಕ್ ಟೆಸ್ಟ್ ಸರಾಸರಿ', strengths: 'ಬಲಗಳು', improvements: 'ಸುಧಾರಣೆ ಬೇಕಾದ ಕ್ಷೇತ್ರಗಳು',
      q_review: 'ಪ್ರಶ್ನೆವಾರು ತಿದ್ದುಪಡಿ', model_answer: 'ಮಾದರಿ ಉತ್ತರ', your_ans: 'ನಿಮ್ಮ ಉತ್ತರ', emotion_profile: 'ಭಾವನೆ ಪ್ರೊಫೈಲ್',
      integrity: 'ಪ್ರಾಮಾಣಿಕತೆ ವರದಿ', print: 'ಪ್ರಿಂಟ್ / PDF ಉಳಿಸಿ', back_dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ',
      language: 'ಭಾಷೆ',
    },
    ta: {
      nav_dashboard: 'டாஷ்போர்டு', nav_mock: 'மாதிரித் தேர்வு', nav_interview: 'நேர்காணல்', nav_history: 'வரலாறு',
      nav_profile: 'சுயவிவரம்', nav_admin: 'நிர்வாகம் / HR', nav_logout: 'வெளியேறு', nav_login: 'உள்நுழை', nav_register: 'பதிவு',
      voice_title: 'குரல் உதவியாளர்', voice_listening: 'கேட்கிறேன்...', voice_try: 'சொல்லுங்கள்: "டாஷ்போர்டு", "மாதிரித் தேர்வு", "நேர்காணல்", "வரலாறு", "வெளியேறு"',
      voice_unsupported: 'இந்த உலாவியில் குரல் ஆதரவு இல்லை. Chrome அல்லது Edge பயன்படுத்தவும்.',
      voice_notheard: 'மன்னிக்கவும், புரியவில்லை. மீண்டும் சொல்லுங்கள்.', voice_login_first: 'முதலில் உள்நுழையவும்.',
      voice_greet_guest: 'வணக்கம்! நான் உங்கள் நேர்காணல் உதவியாளர். உள்நுழை, பதிவு அல்லது மொழி மாற்று என்று சொல்லலாம்.',
      voice_greet_user: 'வணக்கம்! டாஷ்போர்டு, மாதிரித் தேர்வு, நேர்காணல், வரலாறு, சுயவிவரம் அல்லது வெளியேறு என்று சொல்லலாம்.',
      voice_going: 'திறக்கிறேன்', voice_lang_changed: 'மொழி தமிழுக்கு மாற்றப்பட்டது.',
      login_title: 'மீண்டும் வருக', username: 'பயனர் பெயர்', password: 'கடவுச்சொல்', login_btn: 'உள்நுழை',
      no_account: 'கணக்கு இல்லையா?', have_account: 'ஏற்கனவே கணக்கு உள்ளதா?',
      register_title: 'கணக்கை உருவாக்கு', full_name: 'முழு பெயர்', email: 'மின்னஞ்சல்', phone: 'தொலைபேசி (விருப்பம்)',
      resume_opt: 'ரெஸ்யூம் (PDF / DOC / DOCX, விருப்பம்)', register_btn: 'பதிவு செய்',
      dash_title: 'டாஷ்போர்டு', mock_title: 'மாதிரித் தேர்வு', mock_desc: 'கடின நிலைகளுடன் கூடிய பல தேர்வு கேள்விகளில் பயிற்சி',
      start_mock: 'மாதிரித் தேர்வைத் தொடங்கு', int_title: 'நேர்காணல்', int_desc: 'உணர்வு கண்டறிதலுடன் நேரடி AI கண்காணிப்பு நேர்காணல்',
      go_interview: 'நேர்காணலுக்குச் செல்', view_results: 'அனைத்து முடிவுகளையும் பார்', my_resume: 'என் ரெஸ்யூம்', upload_resume: 'ரெஸ்யூமை பதிவேற்று',
      update_profile: 'சுயவிவரத்தைப் புதுப்பி', no_resume: 'இன்னும் ரெஸ்யூம் பதிவேற்றப்படவில்லை', shortlisted_banner: 'நீங்கள் தேர்ந்தெடுக்கப்பட்டுள்ளீர்கள்!',
      messages: 'HR செய்திகள்', recent_interviews: 'சமீபத்திய நேர்காணல் முடிவுகள்',
      att_title: 'AI நேர்காணல்', att_sub: 'உணர்வு பகுப்பாய்வு மற்றும் போலி முக கண்டறிதலுடன் கேமரா நேர்காணல்',
      choose_subject: 'உங்கள் பாடத்தைத் தேர்ந்தெடுக்கவும்', start_interview: 'நேர்காணலைத் தொடங்கு', camera_note: 'நேர்காணலின் போது கேமரா இயக்கத்தில் இருக்க வேண்டும். உணர்வு மற்றும் உயிர்ப்பு சோதனைக்காக படங்கள் பகுப்பாயப்படும்.',
      question: 'கேள்வி', your_answer: 'உங்கள் பதில்', type_or_speak: 'பதிலை தட்டச்சு செய்யவும் அல்லது மைக்கைப் பயன்படுத்தவும்...',
      speak_answer: 'பேசி பதிலளி', stop: 'நிறுத்து', read_q: 'கேள்வியைப் படி', next_q: 'அடுத்த கேள்வி', finish: 'நேர்காணலை முடி',
      live_check: 'உயிர்ப்பு', emotion: 'உணர்வு', camera_on: 'கேமரா இயக்கத்தில்', camera_off: 'கேமரா அணைந்துள்ளது - அனுமதி வழங்கவும்',
      feedback_title: 'நேர்காணல் கருத்து', feedback_sub: 'உங்கள் அனுபவத்தைப் பகிரவும்', rating: 'மதிப்பீடு',
      comments: 'கருத்துகள்', submit_feedback: 'சமர்ப்பித்து முடிவைப் பார்',
      report_card: 'நேர்காணல் அறிக்கை அட்டை', interview_marks: 'நேர்காணல் மதிப்பெண்', personality_marks: 'ஆளுமை மதிப்பெண்',
      overall: 'மொத்த மதிப்பெண்', grade: 'தரம்', mock_avg: 'மாதிரித் தேர்வு சராசரி', strengths: 'பலங்கள்', improvements: 'மேம்படுத்த வேண்டியவை',
      q_review: 'கேள்வி வாரியான திருத்தம்', model_answer: 'மாதிரி பதில்', your_ans: 'உங்கள் பதில்', emotion_profile: 'உணர்வு விவரம்',
      integrity: 'நேர்மை அறிக்கை', print: 'அச்சிடு / PDF சேமி', back_dashboard: 'டாஷ்போர்டுக்குத் திரும்பு',
      language: 'மொழி',
    },
    te: {
      nav_dashboard: 'డ్యాష్‌బోర్డ్', nav_mock: 'మాక్ టెస్ట్', nav_interview: 'ఇంటర్వ్యూ', nav_history: 'చరిత్ర',
      nav_profile: 'ప్రొఫైల్', nav_admin: 'అడ్మిన్ / HR', nav_logout: 'లాగ్ అవుట్', nav_login: 'లాగిన్', nav_register: 'నమోదు',
      voice_title: 'వాయిస్ అసిస్టెంట్', voice_listening: 'వింటున్నాను...', voice_try: 'చెప్పండి: "డ్యాష్‌బోర్డ్", "మాక్ టెస్ట్", "ఇంటర్వ్యూ", "చరిత్ర", "లాగ్ అవుట్"',
      voice_unsupported: 'ఈ బ్రౌజర్‌లో వాయిస్ సపోర్ట్ లేదు. దయచేసి Chrome లేదా Edge ఉపయోగించండి.',
      voice_notheard: 'క్షమించండి, అర్థం కాలేదు. మళ్ళీ చెప్పండి.', voice_login_first: 'దయచేసి ముందు లాగిన్ అవ్వండి.',
      voice_greet_guest: 'నమస్కారం! నేను మీ ఇంటర్వ్యూ అసిస్టెంట్‌ని. లాగిన్, నమోదు లేదా భాష మార్చు అని చెప్పవచ్చు.',
      voice_greet_user: 'నమస్కారం! డ్యాష్‌బోర్డ్, మాక్ టెస్ట్, ఇంటర్వ్యూ, చరిత్ర, ప్రొఫైల్ లేదా లాగ్ అవుట్ అని చెప్పవచ్చు.',
      voice_going: 'తెరుస్తున్నాను', voice_lang_changed: 'భాష తెలుగుకు మార్చబడింది.',
      login_title: 'తిరిగి స్వాగతం', username: 'యూజర్ పేరు', password: 'పాస్‌వర్డ్', login_btn: 'లాగిన్',
      no_account: 'ఖాతా లేదా?', have_account: 'ఇప్పటికే ఖాతా ఉందా?',
      register_title: 'ఖాతా సృష్టించండి', full_name: 'పూర్తి పేరు', email: 'ఇ-మెయిల్', phone: 'ఫోన్ (ఐచ్ఛికం)',
      resume_opt: 'రెజ్యూమె (PDF / DOC / DOCX, ఐచ్ఛికం)', register_btn: 'నమోదు చేయండి',
      dash_title: 'డ్యాష్‌బోర్డ్', mock_title: 'మాక్ టెస్ట్', mock_desc: 'కఠినత స్థాయిల బహుళ ఎంపిక ప్రశ్నలతో సాధన',
      start_mock: 'మాక్ టెస్ట్ ప్రారంభించండి', int_title: 'ఇంటర్వ్యూ', int_desc: 'భావోద్వేగ గుర్తింపుతో లైవ్ AI పర్యవేక్షణ ఇంటర్వ్యూ',
      go_interview: 'ఇంటర్వ్యూకి వెళ్ళండి', view_results: 'అన్ని ఫలితాలు చూడండి', my_resume: 'నా రెజ్యూమె', upload_resume: 'రెజ్యూమె అప్‌లోడ్ చేయండి',
      update_profile: 'ప్రొఫైల్ నవీకరించండి', no_resume: 'ఇంకా రెజ్యూమె అప్‌లోడ్ చేయలేదు', shortlisted_banner: 'మీరు షార్ట్‌లిస్ట్ అయ్యారు!',
      messages: 'HR సందేశాలు', recent_interviews: 'ఇటీవలి ఇంటర్వ్యూ ఫలితాలు',
      att_title: 'AI ఇంటర్వ్యూ', att_sub: 'భావోద్వేగ విశ్లేషణ మరియు నకిలీ ముఖ గుర్తింపుతో కెమెరా ఇంటర్వ్యూ',
      choose_subject: 'మీ సబ్జెక్ట్ ఎంచుకోండి', start_interview: 'ఇంటర్వ్యూ ప్రారంభించండి', camera_note: 'ఇంటర్వ్యూ సమయంలో కెమెరా ఆన్‌లో ఉండాలి. భావోద్వేగం మరియు లైవ్‌నెస్ కోసం ఫ్రేమ్‌లు విశ్లేషించబడతాయి.',
      question: 'ప్రశ్న', your_answer: 'మీ సమాధానం', type_or_speak: 'మీ సమాధానం టైప్ చేయండి లేదా మైక్ ఉపయోగించండి...',
      speak_answer: 'మాట్లాడి సమాధానం ఇవ్వండి', stop: 'ఆపు', read_q: 'ప్రశ్న చదవండి', next_q: 'తదుపరి ప్రశ్న', finish: 'ఇంటర్వ్యూ ముగించండి',
      live_check: 'లైవ్‌నెస్', emotion: 'భావోద్వేగం', camera_on: 'కెమెరా ఆన్', camera_off: 'కెమెరా ఆఫ్ - అనుమతి ఇవ్వండి',
      feedback_title: 'ఇంటర్వ్యూ ఫీడ్‌బ్యాక్', feedback_sub: 'మీ అనుభవాన్ని తెలియజేయండి', rating: 'రేటింగ్',
      comments: 'వ్యాఖ్యలు', submit_feedback: 'సమర్పించి ఫలితం చూడండి',
      report_card: 'ఇంటర్వ్యూ రిపోర్ట్ కార్డ్', interview_marks: 'ఇంటర్వ్యూ మార్కులు', personality_marks: 'వ్యక్తిత్వ మార్కులు',
      overall: 'మొత్తం స్కోరు', grade: 'గ్రేడ్', mock_avg: 'మాక్ టెస్ట్ సగటు', strengths: 'బలాలు', improvements: 'మెరుగుపరచాల్సినవి',
      q_review: 'ప్రశ్నల వారీ దిద్దుబాటు', model_answer: 'నమూనా సమాధానం', your_ans: 'మీ సమాధానం', emotion_profile: 'భావోద్వేగ ప్రొఫైల్',
      integrity: 'నిజాయితీ నివేదిక', print: 'ప్రింట్ / PDF సేవ్', back_dashboard: 'డ్యాష్‌బోర్డ్‌కు తిరిగి',
      language: 'భాష',
    },
  };

  function getLang() { return localStorage.getItem('lang') || 'en'; }
  function t(key) { return (D[getLang()] && D[getLang()][key]) || D.en[key] || key; }
  function apply() {
    const l = getLang();
    document.documentElement.lang = l;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
    document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
    const sel = document.getElementById('langSelect');
    if (sel) sel.value = l;
    document.dispatchEvent(new CustomEvent('langchange', { detail: l }));
  }
  function setLang(l) { if (LANGS[l]) { localStorage.setItem('lang', l); apply(); } }

  window.I18N = { LANGS, D, t, getLang, setLang, apply };
  window.t = t; window.getLang = getLang; window.setLang = setLang;
  document.addEventListener('DOMContentLoaded', () => {
    const sel = document.getElementById('langSelect');
    if (sel) sel.addEventListener('change', e => setLang(e.target.value));
    apply();
  });
})();
