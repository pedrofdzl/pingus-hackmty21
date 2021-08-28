from flask import Flask, render_template, redirect, flash, url_for, request

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'MySuperSecretKey'

# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Clases camelCase
# todo lo demas snake_case

if __name__ == '__main__':
    app.run(debug=True)
