#!C:\Users\fidel\Desktop\phenomes_analysis\venv\Scripts\python.exe

import fileinput
import epitran

epi = epitran.Epitran('uig-Arab')
for line in fileinput.input():
    s = epi.transliterate(line.strip())
    print(s)
