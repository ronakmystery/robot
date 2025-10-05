import RPi.GPIO as GPIO
import time
import math

BUZZER_PIN = 21
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
pwm = GPIO.PWM(BUZZER_PIN, 440)
pwm.start(0)

# --- note helpers ------------------------------------------------------------

# map length symbols to beat fractions
LEN = {
    "w": 4.0,   # whole
    "h": 2.0,   # half
    "q": 1.0,   # quarter
    "e": 0.5,   # eighth
    "s": 0.25,  # sixteenth
    ".": 1.5,   # dotted factor (used as suffix, e.g., "q.")
}

# convert "A4", "C#5", "Db4" to frequency (Hz)
SEMITONE_INDEX = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}
def note_to_freq(name: str) -> float:
    # rest
    if name == "R" or name == "-":
        return 0.0
    # split letter+accidental and octave
    # supports "C#4" / "Db4" / "A4"
    for k in sorted(SEMITONE_INDEX, key=len, reverse=True):
        if name.startswith(k):
            octave = int(name[len(k):])
            n = SEMITONE_INDEX[k] + (octave - 4) * 12  # semitones from C4
            # MIDI number: A4=69, we compute from A4 reference
            midi = 69 + (n - 9)  # since A4 is 9 semitones above C4
            return 440.0 * (2 ** ((midi - 69) / 12.0))
    raise ValueError(f"bad note name: {name}")

def beat_duration_seconds(bpm: float, length_symbol: str) -> float:
    # supports dotted lengths like "q." or "e."
    if length_symbol.endswith("."):
        base = LEN[length_symbol[0]]
        return (60.0 / bpm) * base * LEN["."]
    return (60.0 / bpm) * LEN[length_symbol]

def play_tone(freq: float, duration: float, duty=100):
    if freq <= 1.0:
        pwm.ChangeDutyCycle(0)
        time.sleep(duration)
    else:
        pwm.ChangeFrequency(freq)
        pwm.ChangeDutyCycle(duty)
        time.sleep(duration)
        pwm.ChangeDutyCycle(0)

# --- melody library ----------------------------------------------------------

# format: list of (note_name, length_symbol)
# use "R" (or "-") for rest. examples: "q"=quarter, "e"=eighth, "q."=dotted quarter
SONGS = {
    "tetris_a": [
        ("E5","q"), ("B4","e"), ("C5","e"), ("D5","q"), ("C5","e"), ("B4","e"),
        ("A4","q"), ("A4","e"), ("C5","e"), ("E5","q"), ("D5","e"), ("C5","e"),
        ("B4","q"), ("B4","e"), ("C5","e"), ("D5","q"), ("E5","q"),
        ("C5","q"), ("A4","q"), ("A4","h"),
    ],
    "happy_birthday": [
        ("G4","e"), ("G4","e"), ("A4","q"), ("G4","q"), ("C5","q"), ("B4","h"),
        ("G4","e"), ("G4","e"), ("A4","q"), ("G4","q"), ("D5","q"), ("C5","h"),
        ("G4","e"), ("G4","e"), ("G5","q"), ("E5","q"), ("C5","q"), ("B4","q"), ("A4","q"),
        ("F5","e"), ("F5","e"), ("E5","q"), ("C5","q"), ("D5","q"), ("C5","h"),
    ],
}

def play_song(name: str, bpm=120, duty=50):
    score = SONGS[name]
    for note, length in score:
        freq = note_to_freq(note)
        dur  = beat_duration_seconds(bpm, length)
        play_tone(freq, dur, duty=duty)

# --- run one ---------------------------------------------------------------
if __name__ == "__main__":
    try:
        # pick one:
        # play_song("tetris_a", bpm=120)
        play_song("happy_birthday", bpm=120)
    finally:
        pwm.stop()
        GPIO.cleanup()
