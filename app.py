from flask import Flask, render_template

app = Flask(__name__)

klubbar = [
    {'nafn': 'Fighting Game Klúbbur', 'stofa': '203', 'formadur': 'Matt', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á bardaga tölvuleikjum.'},
    {'nafn': 'Furry Klúbbur', 'stofa': '206', 'formadur': 'Aron', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á furry menningu.'},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/klubbar')
def klubbar():
    return render_template('klubbar.html')


