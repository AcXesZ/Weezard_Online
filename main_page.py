from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import jinja2


app = Flask(__name__, template_folder="templates")
app.config.from_object(__name__)
# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'



@app.route('/')
def hello_world():
    return render_template('prod_table.html')


if __name__ == '__main__':
    app.run()
