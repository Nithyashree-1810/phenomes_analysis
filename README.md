ARCHITECTURE OF PRONOUNCIATION ANALYSIS MODEL:


1.  User Audio
   (m4a, mp3, aac) ----> Input base64 audio file
      │
      ↓
2. Audio Conversion
   *pydub --> converts input audiofile to wav(waveform audio file format)
   *ffmpeg --> decodes audio

      │
      ↓
3. Speech Recognition
   (Whisper Model – small.en)
         * audio → text
         * supports multiple accents
      │
      ↓
4. Transcript Text
      *output of whispher model
      │
      ↓
5. Text Normalization
      - clean words
      - numbers are converted to words (using num2words python library)
      │
      ↓
6. Phoneme Conversion
     (epitran python library)
       - converts text to phonemes
       - to analyze pronunciation mistakes
      │
      ↓
7. Phone Alignment
    (Sequence Matcher – built-in python library)
         - to compare phoneme sequences
         - to detect mispronunciations
      │
      ↓
8. Error Detection
      │
      ↓
9. Score + Tips
     Score = (Sum of phoneme similarity scores) / (Total phonemes)
      │
      ↓
10. Output
    - misprounced words
    - position of misprounced words
    -  overall scoring
    -  tips to improve for particular mistakes
    -  overall tips to improve
   
Additional libraries used:
   - Langdetect (to detect language of the refernce passage)
   - Panphon (phonetics library which as feature vector)

    
