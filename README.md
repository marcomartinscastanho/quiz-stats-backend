# quiz-stats

## Categories

1. Science
    - Biology
    - Technology
    - Chemistry
    - Inventions
    - Mathematics
    - Physics
    - Animals
    - Space
    - General Science
2. History
     - Wars
     - Civilizations
     - Kings/Presidents
     - Historical Events
     - General History
3. Geography
    - Capitals
    - Contries
    - Flags
    - Landmarks
    - Mountains
    - Bodies of Water
    - General Geography
4. Arts/Entertainment
    - Architecture
    - Film/TV
    - Photography
    - Theatre
    - Music
    - Video Games
    - Modern Art
    - Literature
    - Sculpture
    - Painting
    - Opera
    - General Arts/Entertainment
5. Sports
    - Olympics
    - Soccer
    - Basketball
    - Sports Records
    - Motor Sports
    - General Sports
6. Language
    - Foreign Languages
    - Grammar
    - Idioms
    - Etymology
    - Riddles
    - General Language
7. Pop Culture
    - Celebreties
    - Memes
    - Brands
    - Food
    - Fashion
    - General Pop Culture
8. Current Events
    - Politics
    - News
    - Laws
    - Elections
    - General Current Events
9. Humanities
    - Mythology
    - Philosophy
    - Religion
    - General Humanities

## Predictor

The goal of the predictor is to predict:

1. the order in which we should play
2. the best topics for each player
3. the best topics for the team as a whole

### Input

- the topics of the first part
- the topics of the second part
- who's playing today

### Process

#### 1. Auto-categorization of Topics

We input the topics of each part.  
ChatGPT does an initial quick attempt to auto-categorize the 24 topics (12 in each part).  
Categories are the sub-categories above - we want to be specific here.

#### 2. Manual veririfaction of categories

The predictor page should display the 24 topics of the game with their auto-determined categories in a dropdown selector.  
We should manually verify them and fix some that we don't agree with.  

#### 3. Order of play

We've been doing well on this so far:

- the least good player plays first - can do better with more topics to choose from
- the best player plays last - can still do well even with fewer topics to choose from
- i.e. players are sorted by their aptitude to the categories in this game

So, the inputs here are:

- players who are playing today
- categories of today's topics (with duplicates - if today's game has multiple topics in the same categories, that's important to know)

It should calculate each player's aptitude to today's game.  
Aptitude should be a weighted median of the player's score in today's categories.  
It should return the players listed from least apt to most apt.

#### 4. Topics per player

Based on the same inputs, it should give, for each player, all topics of each part sorted for this individual player - best topic for this player to worst topic for this player.  
Each player should take note of their topic order, so that they know what to choose when some topics are no longer available.

Potentially include the team results in the mix, so that the order also takes into account how the colleagues may be able to assist in case of rebounds.  
So perhaps the order should be: (xTplayer, xTteam)

##### 5. Topics per team

When all players have played their indiviual questions, 4 topics are left.  
It's impossible to predict which ones will be left.

All we can do here is sort all topics in each part by team aptitude.  
Someone (captain) takes note of these.  
When there's only 4 left, we'll know which ones are the best for us.
