#!/usr/bin/env python3
"""Render every scripts/*.json into audio/<stem>/<id>.wav with Google Chirp 3 HD.

Script format:
{"lang": "it-IT", "voice": "Charon", "rate": 1.0,
 "lines": {"A01": "text", "A02": {"text": "...", "rate": 1.08, "voice": "Puck"}}}

Brand names are spoken via pronunciation.json (e.g. Cosy2Go -> "Cosy to Go"); the script text
(used for subtitles) keeps the written name.
A line is only re-synthesised when its spoken text/voice/rate changed (audio/<stem>/manifest.json).
The key comes from the env var GOOGLE_TTS_KEY (GitHub Actions secret) and is never written anywhere.
"""
import base64, glob, hashlib, json, os, sys, urllib.request, urllib.error

KEY = os.environ.get('GOOGLE_TTS_KEY', '').strip()
if not KEY:
    sys.exit('GOOGLE_TTS_KEY is not set')

PRON = json.load(open('pronunciation.json', encoding='utf-8')) if os.path.exists('pronunciation.json') else {}

def spoken(lang, text):
    table = dict(PRON.get('*', {})); table.update(PRON.get(lang.split('-')[0], {}))
    for k in sorted(table, key=len, reverse=True):
        text = text.replace(k, table[k])
    return text

def synth(lang, voice, text, rate):
    body = {'input': {'text': text},
            'voice': {'languageCode': lang, 'name': f'{lang}-Chirp3-HD-{voice}'},
            'audioConfig': {'audioEncoding': 'LINEAR16', 'sampleRateHertz': 48000, 'speakingRate': rate}}
    req = urllib.request.Request('https://texttospeech.googleapis.com/v1/text:synthesize',
                                 data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': KEY})
    try:
        return base64.b64decode(json.load(urllib.request.urlopen(req, timeout=90))['audioContent'])
    except urllib.error.HTTPError as e:
        raise SystemExit(f'TTS error {e.code}: {e.read().decode()[:300]}')

chars = 0
files = sys.argv[1:] or sorted(glob.glob('scripts/*.json'))
for path in files:
    s = json.load(open(path, encoding='utf-8'))
    stem = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join('audio', stem); os.makedirs(out, exist_ok=True)
    mpath = os.path.join(out, 'manifest.json')
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for lid, line in s['lines'].items():
        if isinstance(line, str): line = {'text': line}
        text = spoken(s['lang'], line.get('say', line['text']))
        voice = line.get('voice', s.get('voice', 'Charon')); rate = line.get('rate', s.get('rate', 1.0))
        h = hashlib.sha1(json.dumps([s['lang'], voice, rate, text], ensure_ascii=False).encode()).hexdigest()[:12]
        wav = os.path.join(out, f'{lid}.wav')
        if man.get(lid) == h and os.path.exists(wav):
            continue
        open(wav, 'wb').write(synth(s['lang'], voice, text, rate)); chars += len(text)
        man[lid] = h; print(f'{stem}/{lid} {voice} {rate}: {text}')
    for lid in list(man):
        if lid not in s['lines']:
            man.pop(lid); p = os.path.join(out, f'{lid}.wav')
            if os.path.exists(p): os.remove(p)
    json.dump(man, open(mpath, 'w'), indent=1, sort_keys=True)
print('characters synthesised:', chars)
