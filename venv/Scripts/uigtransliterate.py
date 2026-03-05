#!C:\Users\fidel\task1\venv\Scripts\python.exe

import fileinput
import epitran

epi = epitran.Epitran('uig-Arab')
for line in fileinput.input():
    s = epi.transliterate(line.strip())
    print(s)
