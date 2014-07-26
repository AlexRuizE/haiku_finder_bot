haiku_finder_bot
================

This short script finds accidental haikus in Reddit's comments, and posts them as a reply. 

It first generates a dictionary of syllables per word inferring the number of syllables from the phonemic structure of the word and its lexical stresses (using the Carnegie Mellon University's pronunciation dictionary). 

It then retrieves the comments on Reddit's \r\all section as json data, searches for the 5-7-5 syllabic structure, and accesses the Reddit API to post the properly formatted haiku as a reply to the original comment.

