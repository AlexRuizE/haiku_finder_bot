import re, requests, collections, praw, time

words=list()                                        
syl=collections.OrderedDict()


###############################################################################################################
# Generate syllables dictionary using Carnegie Mellon University's pronunciation dictionary (n=133,389 words) #
###############################################################################################################

cmudict=urllib.request.urlopen('http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict.0.7a').read()
cmudict=cmudict.decode('utf8')
cmudict=cmudict.lower().split('\n')

unclutter=[i for j in (range(66), range(71, 73), range(75,83), range(86,118), range(119,125), range(133383,133388))  for i in j]
cmudict=[cmudict[i] for i in range(0,133388) if i not in unclutter]     # Clean file from headers and footers.

x=[re.findall('\s{2}', i) for i in cmudict]
print('Length of word/phonemes divisions is same as length of list: ', len(x)==len(cmudict))    # If true it means that every word
del x                                                                                           # has indeed two whitespaces
                                                                                                # before the actual pronunciation,
                                                                                                # so we can safely use these spaces
                                                                                                # as separators.

words=[re.findall('(\w*\'?-?\w+?)\s{2}(.*)', i) for i in cmudict]   # Separate cmudict into words and its phonemes. Words with many
                                                                    # acceptions will have (1), (2) or (3) in their name, indicating
                                                                    # the number of acceptions. These cases are eliminated in 
                                                                    # the next loop with the 'if' test.

for i in list(range(len(words))):                                           # For each word/phoneme pair, generate a dictionary entry 
    if words[i]:                                                            # with the word as key, and number of lexical stresses
        syl[words[i][0][0]] = len(re.sub('[a-z\s+]', '', words[i][0][1]))   # (number of syllables) as value. 




#########################################
## Login to Reddit and retrieve \r\all ##
#########################################

### Using requests instead of urllib ###
headers={'User-Agent': 'Script to find and post accidental haikus in user comments by your_user_name'}
req = requests.get('http://www.reddit.com/r/all/.json', allow_redirects=False, headers=headers)
links=re.findall('permalink\": \"(.*?)\"', req.text) 

# Login and retrieve first 25 submission in \r\all
user_agent='Script to find and post accidental haikus in user comments by /u/pinchewero'
r=praw.Reddit(user_agent=user_agent)
username='your_user_name'
password='your_password'
r.login(username=username, password=password) 
#submissions = r.get_subreddit('test').get_hot(limit=5)
submissions = r.get_subreddit('all').get_hot(limit=25)
submission = next(submissions)
already_done=set()
banned=['funny','politics','atheism', 'AskReddit', 'aww', 'wheredidthesodago', 'Minecraft', 'comics', 'technology', 'pics', 'IAmA'] # Add subreddits that might ban your bot



######################### 
# Find and reply haikus #
#########################

for link in links:

    urljson='http://www.reddit.com'+link+'.json'

    if not re.findall('/r/(\w+)/', urljson)[0] in banned:
        comments_raw=requests.get(urljson, allow_redirects=False, headers=headers)
        comments_raw.connection.close()
        comments=re.findall('"body": "(.*?)",', comments_raw.text)   # Extract comments from json file

        for i in range(len(comments)):                      
            for ch in ['\\n']:                      # Clean up text a bit
                if ch in comments[i]:
                    comments[i]=comments[i].replace(ch, ' ')
            for ch in [',', '\\']:
                if ch in comments[i]:
                    comments[i]=comments[i].replace(ch, '')

        haikus=[]
        line_markers_for_haikus=[]
        haikus_found=0 

        for c in range(len(comments)):
            sentence_markers=[dots.start() for dots in re.finditer('(?<!\.)[.?!](?!\.)', comments[c])]   #(?<!\.)[\.\!\?](?=\s+\w+)
            start_sentence=0
            for s in range(len(sentence_markers)):
                end_sentence=sentence_markers[s]
                sentence=''.join([comments[c][i] for i in range(start_sentence,end_sentence)])
                words_per_sentence=''.join([comments[c][i] for i in range(start_sentence,end_sentence)]).split() 
                syl_per_sentence=[syl[word.lower()] if word.lower() in syl.keys() else -100 for word in words_per_sentence]
                if sum(syl_per_sentence) == 17:        # Minimal number of syllables for a haiku to appear
                        word=0     # Counter for words index in each comment
                        syllables=0     # Counter for syllables
                        while syllables<5:
                            syllables+=syl_per_sentence[word]
                            word+=1
                        line_marker_1=word    
                        if syllables==5:                                        # 5 syllables
                            syllables=0
                            while syllables<7:
                                syllables+=syl_per_sentence[word]
                                word+=1
                            line_marker_2=word
                            if syllables==7:                                    # 7 syllables
                                syllables=0
                                while syllables<5:                           
                                    syllables+=syl_per_sentence[word]
                                    word+=1
                                if syllables==5:                                # 5 syllables
                                    haikus.append([sentence])
                                    line_markers_for_haikus.append([line_marker_1,line_marker_2])
                                    haikus_found+=1
                start_sentence=end_sentence+2 # The period and the space after that.

        print(haikus)

        if len(haikus)>0:
            flat_comments = praw.helpers.flatten_tree(submission.comments)
            for h in range(len(haikus)):
                words_in_haiku=str(haikus[h]).strip('["]').split()

                line1=' '.join(words_in_haiku[:line_markers_for_haikus[h][0]])
                line2=' '.join(words_in_haiku[line_markers_for_haikus[h][0]:line_markers_for_haikus[h][1]])
                line3=' '.join(words_in_haiku[line_markers_for_haikus[h][1]:])

                for i in range(len(flat_comments)):
                    if (not isinstance(flat_comments[i], praw.objects.MoreComments) and str(haikus[h]).strip('["]')[3:20] in flat_comments[i].body):
                        text_replied='    '+line1+'\n    '+line2+'\n    '+line3
                        flat_comments[i].reply(text_replied)
                        time.sleep(5)

    time.sleep(5)
    try:    
        submission = next(submissions)
    except StopIteration:
        r.clear_authentication()
        r.http.close() 
        print("\n\n\nNo more links to search. Bye!\n\n\n")
        break



