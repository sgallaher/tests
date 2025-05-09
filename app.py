from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tests.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(10), unique=True, nullable=False)
    words = db.Column(db.String(150), nullable=False)  # Comma-separated words
    grades = db.Column(db.String(50), nullable=False)  # Comma-separated grades

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    scores = db.Column(db.String(50), nullable=False)  # Comma-separated scores

# Initialize database
with app.app_context():
    db.create_all()

# Home page with pagination
@app.route('/')
def index():
    puzzle = []
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of tests per page
    pagination = Test.query.order_by(Test.id.desc()).paginate(page=page, per_page=per_page)
    recent_tests = pagination.items
    has_next = pagination.has_next
    return render_template("index.html", puzzle=puzzle, recent_tests=recent_tests, page=page, has_next=has_next)

# Accessing a test
@app.route('/test/<token>')
def home(token):
    if not token:
        return "Token is required to access a test.", 400

    test = Test.query.filter_by(token=token).first()
    if not test:
        return "Invalid token.", 404

    words = test.words.split(',')
    puzzle = []
    for word in words:
        num = len(word) // 3
        hints = []
        while len(hints) < num:
            c = randint(0, len(word) - 1)
            if c not in hints:
                hints.append(c)
        puzzle.append([word, hints])

    return render_template("index.html", puzzle=puzzle, token=token)

# Creating a test
@app.route('/create-test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
        token = os.urandom(4).hex()
        words = request.form.get('words')
        grades = request.form.get('grades')

        # Remove spaces from each word
        words = ','.join(word.strip() for word in words.split(','))

        if len(words.split(',')) > 10 or any(len(word) > 15 for word in words.split(',')):
            return "Each test can have up to 10 words, each no more than 15 characters.", 400

        test = Test(token=token, words=words, grades=grades)
        db.session.add(test)
        db.session.commit()

        # Redirect to a new template with the test URL
        test_url = url_for('home', token=token, _external=True)
        return render_template("test_created.html", test_url=test_url)

    return render_template("createtest.html")

# Submitting a test
@app.route('/submit-test', methods=['POST'])
def submit_test():
    name = request.form.get('name')
    token = request.form.get('token')
    scores = request.form.get('scores')  # Comma-separated scores

    # Fetch the test by token
    test = Test.query.filter_by(token=token).first()
    if not test:
        return "Invalid token.", 404

    # Save the user's attempt
    attempt = Attempt(test_id=test.id, name=name, scores=scores)
    db.session.add(attempt)
    db.session.commit()

    # Calculate the user's total score
    user_score = sum(map(int, scores.split(',')))

    # Fetch all attempts for the test and calculate scores
    attempts = Attempt.query.filter_by(test_id=test.id).all()
    all_scores = sorted(
        [(attempt.name, sum(map(int, attempt.scores.split(',')))) for attempt in attempts],
        key=lambda x: x[1],
        reverse=True
    )

    # Find the user's position
    user_position = next((i + 1 for i, (_, score) in enumerate(all_scores) if score == user_score), None)
    if user_position is None:
        return "User score not found in the rankings.", 404

    # Pagination logic
    per_page = 10
    start_index = ((user_position - 1) // per_page) * per_page
    end_index = start_index + per_page
    paginated_scores = all_scores[start_index:end_index]

    # Determine if there are previous/next pages
    has_previous = start_index > 0
    has_next = end_index < len(all_scores)

    # Render the success page with the ranked scores
    return render_template(
        "success.html",
        scores=paginated_scores,
        user_position=user_position,
        user_score=user_score,
        has_previous=has_previous,
        has_next=has_next,
        start_index=start_index,
        token=token
    )

@app.route('/test-scores/<token>/<int:user_score>')
def test_scores(token, user_score):
    # Fetch the test by token
    test = Test.query.filter_by(token=token).first()
    if not test:
        return "Invalid token.", 404

    # Fetch all attempts for the test and calculate scores
    attempts = Attempt.query.filter_by(test_id=test.id).all()
    all_scores = sorted(
        [(attempt.name, sum(map(int, attempt.scores.split(',')))) for attempt in attempts],
        key=lambda x: x[1],
        reverse=True
    )

    # Get the start index from the query parameter (default to 0)
    start_index = int(request.args.get('start', 0))

    # Pagination logic
    per_page = 10
    end_index = start_index + per_page
    paginated_scores = all_scores[start_index:end_index]

    # Determine if there are previous/next pages
    has_previous = start_index > 0
    has_next = end_index < len(all_scores)

    # Find the user's position
    user_position = next((i + 1 for i, (_, score) in enumerate(all_scores) if score == user_score), None)

    # Render the success page with the ranked scores
    return render_template(
        "success.html",
        scores=paginated_scores,
        user_position=user_position,
        user_score=user_score,
        has_previous=has_previous,
        has_next=has_next,
        start_index=start_index,
        token=token
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
