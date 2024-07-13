#!/usr/bin/env python
# coding: utf-8

import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
from googletrans import Translator
from spacy.matcher import Matcher
import pandas as pd
import numpy as np


# In[3]:


nlp = spacy.load("nl_core_news_md")
nlp.add_pipe('spacytextblob')


# In[4]:


print(nlp.pipeline)
# [('tok2vec', <spacy.pipeline.Tok2Vec>), ('tagger', <spacy.pipeline.Tagger>), ('parser', <spacy.pipeline.DependencyParser>), ('ner', <spacy.pipeline.EntityRecognizer>), ('attribute_ruler', <spacy.pipeline.AttributeRuler>), ('lemmatizer', <spacy.lang.en.lemmatizer.EnglishLemmatizer>)]
print(nlp.pipe_names)
# ['tok2vec', 'tagger', 'parser', 'ner', 'attribute_ruler', 'lemmatizer']


# In[9]:


text = 'I had a really horrible day. It was the worst day ever! But every now and then I have a really good day that makes me happy.'
dutch_text = 'Ik zou liegen als ik zei dat ik het niet naar mijn zin had vandaag'

translator = Translator()
translated_text = translator.translate(dutch_text).text
print(translated_text)

doc = nlp(translated_text)
print(doc._.blob.polarity)                            # Polarity: -0.125
print(doc._.blob.subjectivity)                        # Subjectivity: 0.9
print(doc._.blob.sentiment_assessments.assessments)   # Assessments: [(['really', 'horrible'], -1.0, 1.0, None), (['worst', '!'], -1.0, 1.0, None), (['really', 'good'], 0.7, 0.6000000000000001, None), (['happy'], 0.8, 1.0, None)]
doc._.blob.ngrams()                            # [WordList(['I', 'had', 'a']), WordList(['had', 'a', 'really']), WordList(['a', 'really', 'horrible']), WordList(['really', 'horrible', 'day']), WordList(['horrible', 'day', 'It']), WordList(['day', 'It', 'was']), WordList(['It', 'was', 'the']), WordList(['was', 'the', 'worst']), WordList(['the', 'worst', 'day']), WordList(['worst', 'day', 'ever']), WordList(['day', 'ever', 'But']), WordList(['ever', 'But', 'every']), WordList(['But', 'every', 'now']), WordList(['every', 'now', 'and']), WordList(['now', 'and', 'then']), WordList(['and', 'then', 'I']), WordList(['then', 'I', 'have']), WordList(['I', 'have', 'a']), WordList(['have', 'a', 'really']), WordList(['a', 'really', 'good']), WordList(['really', 'good', 'day']), WordList(['good', 'day', 'that']), WordList(['day', 'that', 'makes']), WordList(['that', 'makes', 'me']), WordList(['makes', 'me', 'happy'])]


# In[63]:


words = pd.read_csv('woorden.txt', delimiter='\t')
ja = np.char.split(words['Ja (Nederlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
ja_eng = np.char.split(words['Ja (Buitenlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
ja = np.append(ja, ja_eng)

nee = np.char.split(words['Nee (Nederlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
nee_eng = np.char.split(words['Nee (Buitenlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
nee = np.append(nee, nee_eng)

misschien = np.char.split(words['Misschien (Nederlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
miss_eng = np.char.split(words['Misschien (Buitenlands)'].dropna().apply(str.lower).to_numpy(dtype=str))
misschien = np.append(misschien, miss_eng)

pat_ja, pat_nee, pat_miss = [], [], []
for phrase in ja:
    pat_ja.append([{"LOWER": token} for token in phrase])
for phrase in nee:
    pat_nee.append([{"LOWER": token} for token in phrase])
for phrase in misschien:
    pat_miss.append([{"LOWER": token} for token in phrase])

print(pat_ja)


# In[64]:


# To-do: Look if there are other packages like spacy textblob for other purposes than sentiment analysis

matcher = Matcher(nlp.vocab)
'''
# Add match ID "HelloWorld" with no callback and one pattern
pattern = [{"LOWER": "hallo"}, {"IS_PUNCT": True}, {"LOWER": "wereld"}, {"IS_PUNCT": True}]
matcher.add("HW", [pattern])
doc2 = nlp("hallo; wereld! hallo wereld!")
'''

text = 'Ja nee dat heb ik niet gedaan'
doc = nlp(text)
'''
pattern = [{"LOWER": "ja"}]
matcher.add("Positive", [pattern])

pattern1 = [{"LOWER": "nee"}]
pattern2 = [{"LOWER": "niet"}]
matcher.add("Negative", [pattern1, pattern2])
'''
matcher.add("Affirmative", pat_ja)
matcher.add("Negative", pat_nee)
matcher.add("Maybetive", pat_miss)

matches = matcher(doc)
p_counter = 0
n_counter = 0
m_counter = 0
for match_id, start, end in matches:
    string_id = nlp.vocab.strings[match_id]  # Get string representation
    span = doc[start:end]  # The matched span
    print(match_id, string_id, start, end, span.text)
    if(string_id=="Affirmative"):
        p_counter += (1 + end)
    elif(string_id=="Negative"):
        n_counter += (1 + end)
    else:
        m_counter += (1 + end)


# In[65]:


# Classify the answer by comparing the number of affirmative and negative segments, weighing them higher if they appear later

print("Positive counter: " + str(p_counter))
print("Negative counter: " + str(n_counter))

if(p_counter > n_counter):
    print("The answer is affirmative")
elif(p_counter < n_counter):
    print("The answer is negative")
else:
    print("the answer is not clear")
    


# In[53]:




