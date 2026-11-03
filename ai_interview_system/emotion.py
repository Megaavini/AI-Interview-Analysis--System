# -------------------------------
# emotion.py - DeepFace emotion analysis + personality scoring
# -------------------------------
import threading

_lock = threading.Lock()
_deepface = None
_err = None

EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']


def _get():
    global _deepface, _err
    if _deepface is None and _err is None:
        with _lock:
            if _deepface is None and _err is None:
                try:
                    from deepface import DeepFace
                    _deepface = DeepFace
                except Exception as e:
                    _err = str(e)
    return _deepface


def status():
    _get()
    return (_deepface is not None), _err


last_error = None


def analyze(frame_bgr, box=None):
    """
    Returns (dominant_emotion, scores_dict) or (None, None) if it fails (reason in emotion.last_error).
    If a face box (x, y, w, h) is given, only that face (+ margin) is analysed - faster and more reliable.
    """
    global last_error
    df = _get()
    if df is None:
        last_error = 'DeepFace is not installed: ' + str(_err)[:200]
        return None, None
    img = frame_bgr
    if box:
        x, y, w, h = box
        m = int(0.25 * max(w, h))
        H, W = frame_bgr.shape[:2]
        img = frame_bgr[max(0, y - m):min(H, y + h + m), max(0, x - m):min(W, x + w + m)]
    try:
        try:
            res = df.analyze(img, actions=['emotion'], enforce_detection=False,
                             detector_backend='opencv', silent=True)
        except TypeError:                       # older DeepFace has no "silent" argument
            res = df.analyze(img, actions=['emotion'], enforce_detection=False, detector_backend='opencv')
        if isinstance(res, list):
            res = res[0]
        last_error = None
        return res['dominant_emotion'], {k: float(v) for k, v in res['emotion'].items()}
    except Exception as e:
        last_error = f'{type(e).__name__}: {str(e)[:200]}'
        return None, None


def personality_score(counts, total_frames, face_frames, spoof_frames, multi_face_frames, tab_switches):
    """
    Heuristic personality / presence score (0-50) built from emotion samples.
    This is an INDICATIVE behavioural score, not a psychological assessment.

      composure   (0-20): share of calm/positive expressions (neutral + happy)
      positivity  (0-10): share of happy expressions (capped, ~30% happy = full marks)
      stress ctrl (0-10): low share of angry/fear/sad/disgust
      engagement  (0-10): face visible in frame most of the time
      integrity penalty : spoof / multiple faces / tab switching reduce the total
    Returns dict with sub-scores, total and traits.
    """
    n = sum(counts.values())
    if n == 0 or total_frames == 0:
        return {'composure': 0, 'positivity': 0, 'stress_control': 0, 'engagement': 0,
                'penalty': 0, 'total': 0, 'traits': ['Not enough camera data to assess personality.'],
                'confidence_pct': 0, 'stress_pct': 0, 'positive_pct': 0}
    share = {e: counts.get(e, 0) / n for e in EMOTIONS}
    calm = share['neutral'] + share['happy']
    neg = share['angry'] + share['fear'] + share['sad'] + share['disgust']

    composure = round(20 * calm, 1)
    positivity = round(10 * min(1.0, share['happy'] / 0.30), 1)
    stress_control = round(10 * max(0.0, 1 - neg / 0.5), 1)   # >=50% negative -> 0
    engagement = round(10 * (face_frames / total_frames), 1)

    penalty = 0.0
    if total_frames:
        penalty += min(20, 40 * spoof_frames / total_frames)
        penalty += min(5, 10 * multi_face_frames / total_frames)
    penalty += min(5, 1.5 * tab_switches)
    penalty = round(penalty, 1)

    total = max(0.0, round(composure + positivity + stress_control + engagement - penalty, 1))

    traits = []
    if calm >= 0.75:
        traits.append('Calm and composed under questioning')
    elif calm < 0.5:
        traits.append('Showed visible tension during the interview')
    if share['happy'] >= 0.2:
        traits.append('Friendly, positive expressions')
    elif share['happy'] < 0.05:
        traits.append('Could smile / show warmth a little more')
    if neg >= 0.3:
        traits.append('Frequent stress-related expressions (fear / sadness / anger)')
    if share['surprise'] >= 0.2:
        traits.append('Often looked surprised or unsure')
    if face_frames / total_frames < 0.8:
        traits.append('Often looked away from / left the camera')
    if not traits:
        traits.append('Balanced and steady presence')

    return {'composure': composure, 'positivity': positivity, 'stress_control': stress_control,
            'engagement': engagement, 'penalty': penalty, 'total': total, 'traits': traits,
            'confidence_pct': round(calm * 100, 1), 'stress_pct': round(neg * 100, 1),
            'positive_pct': round(share['happy'] * 100, 1)}
