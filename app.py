from flask import Flask, render_template
from random import randint,choice
app = Flask(__name__)
@app.route('/')
def home():
    words = ["cat", "dog", "plane", "train", "bus", "car", "horse","house", "mouse"]
    #create the puzzle 2d array
    puzzle=[]
    #make a unique order of words
    order=[]
    while len(order)<len(words):
        select=choice(words)
        if select not in order:
            order.append(select)
            #get the number of hints (a third of the length of the word)
            num=len(select)//3
            #get the hints for this word
            hints=[]
            while len(hints)<num:
                c=randint(0,len(select)-1)
                if c not in hints:
                    hints.append(c)
            puzzle.append([select,hints])
        
    return render_template("index.html", puzzle=puzzle)
