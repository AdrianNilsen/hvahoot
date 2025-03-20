from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'hemmelig'
users = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if users.get(request.form['username']) == request.form['password']:
            session['user'] = request.form['username']
            return redirect('/welcome')
    return '<form method="post">Brukernavn: <input name="username"> Passord: <input name="password" type="password"> <button type="submit">Login</button></form>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users[request.form['username']] = request.form['password']
        return redirect('/')
    return '<form method="post">Brukernavn: <input name="username"> Passord: <input name="password" type="password"> <button type="submit">Registrer</button></form>'

@app.route('/welcome')
def welcome():
    return f'Velkommen {session.get("user", "Gjest")}! <a href="/">Logg ut</a>'

if __name__ == '__main__':
    app.run(debug=True)
