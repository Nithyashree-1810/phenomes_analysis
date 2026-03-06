ARCHITECTURE OF PRONOUNCIATION ANALYSIS MODEL:

User Audio (m4a, mp3, aac)  ---->  Input base64 audio file


Audio Conversion
* pydub  --> converts input audio file to wav (waveform audio file format)
* ffmpeg --> decodes audio


Speech Recognition (Whisper Model – small.en)
* audio → text
* supports multiple accents


Transcript Text
* output of whisper model


Text Normalization
* clean words
* numbers are converted to words (using num2words python library)


Phoneme Conversion (epitran python library)
* converts text to phonemes
* to analyze pronunciation mistakes


Phone Alignment (Sequence Matcher – built-in python library)
* to compare phoneme sequences
* to detect mispronunciations


Error Detection


Score + Tips
Score = (Sum of phoneme similarity scores) / (Total phonemes)


Output
* mispronounced words
* position of mispronounced words
* overall scoring
* tips to improve for particular mistakes
* overall tips to improve


Additional libraries used:

Langdetect
(to detect language of the reference passage)

Panphon
(phonetics library which has feature vector)