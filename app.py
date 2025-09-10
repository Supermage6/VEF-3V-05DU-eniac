from flask import Flask, render_template

app = Flask(__name__)

klubbar = [
    {'nafn': 'Fighting Game Klúbbur', 'stofa': '203', 'formadur': 'Matt', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á bardaga tölvuleikjum.'},
    {'nafn': 'Furry Klúbbur', 'stofa': '206', 'formadur': 'Aron', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á furry menningu.'},
    {'nafn': 'Tónlistarklúbbur', 'stofa': 'Hátíðarsalur', 'formadur': 'Emily', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á tónlist og spilamennsku.'},
    {'nafn': 'Nördaklúbbur', 'stofa': '202', 'formadur': 'Ösp og Kormákur', 'desc': 'Klúbbur fyrir alla nörda og áhugafólk um ýmislegt nördalegt.'},
    {'nafn': 'Anime og Cosplay Klúbbur', 'stofa': '205', 'formadur': 'Sky', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á anime og cosplay.'},
    {'nafn': 'Warhammer Klúbbur', 'stofa': '302', 'formadur': '???', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Warhammer borðspilinu.'},
    {'nafn': 'D&D Klúbbur', 'stofa': 'fer eftir hóp', 'formadur': 'Frosti', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Dungeons & Dragons borðspilinu.'}
]

@app.route('/')
def home():
    return render_template('main_page.html')

@app.route('/klubbar')
def klubbar():
    return render_template('klubbar.html', k = klubbar)

@app.route('/dagskra')
def dagskra():
    return render_template('dagskra.html')

@app.errorhandler(404)
def page_not_found():
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True)