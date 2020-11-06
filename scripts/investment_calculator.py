from flask import Flask, render_template, session, url_for, redirect
import numpy as np 
import pandas as pd 
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
from wtforms.validators import NumberRange
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.colors import LinearSegmentedColormap
from io import StringIO, BytesIO
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

# def simulate(principal, time, year_interest, monthly_contribution):
def simulate(sample_json):
    year_interest = sample_json["int_rate"]/100
    monthly_contribution = sample_json["mon_amount"]
    principal = sample_json["principal"]
    time = sample_json["time"]
    target = sample_json["target"]
    currency = sample_json["currency"]
    # cumulative = []
    # cumulative.append(principal)
    # monthly = []
    for month in range(time*12):
        principal = principal*(1+(year_interest/12))
        # cumulative.append(principal)
        # monthly.append(month)
        principal += monthly_contribution
    return round(principal, 2)

class FinanceForm(FlaskForm):
    int_rate = TextField("Interest Rate %", id='myfont')
    mon_amount = TextField("Monthly Deposit")
    principal = TextField("Principal")
    time = TextField("Time")
    target = TextField("Target")
    currency = TextField("Currency")

    submit = SubmitField("Calculate")


@app.route("/", methods = ['GET','POST'])
def index():
    form = FinanceForm()
    if form.validate_on_submit():
        session['int_rate'] = form.int_rate.data 
        session['mon_amount'] = form.mon_amount.data
        session['principal'] = form.principal.data    
        session['time'] = form.time.data   
        session['target'] = form.target.data   
        session['currency'] = form.currency.data   
        return redirect(url_for("prediction"))
    return render_template('home.html', form=form)

@app.route('/prediction')#, methods=['POST'])
def prediction():
    content = {}

    content['int_rate'] = int(session['int_rate'])
    content['mon_amount'] = int(session['mon_amount'])
    content['principal'] = int(session['principal'])
    content['time'] = int(session['time'])
    content['target'] = int(session['target'])
    content['currency'] = str(session['currency'])

    results = simulate(content)

    payment_matrix = pd.DataFrame(index = range(0,55000,5000),columns=range(0,1050,50))
    for i in payment_matrix.index:
        for j in payment_matrix.columns:
            content['principal'] = int(i)
            content['mon_amount'] = int(j)
            payment_matrix.loc[i,j] = simulate(content)
    binary = payment_matrix.applymap(lambda x: 0 if x < content['target'] else 1)

    output = BytesIO()
    # fig,ax=plt.subplots(figsize=(6,6))
    f = plt.figure()
    # Define colors
    colors = ((0.0, 0.0, 0.0), (1.0, 0.99, 0.56))
    cmap = LinearSegmentedColormap.from_list('Custom', colors, len(colors))
    ax = sns.heatmap(binary, cmap=cmap)


    # Set the colorbar labels
    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks([0.25,0.75])
    colorbar.set_ticklabels(['0', '1'])
    # plt.savefig('myplot.png')
    canvas = FigureCanvas(f)
    canvas.print_png(output)
    plot_data = base64.b64encode(output.getvalue()).decode('ascii')
    output.seek(0)
    # img = BytesIO()
    # fig.savefig(img, format='png')
    # img.seek(0)
    # # fig.savefig('my_heatmap.png', format='png')
    # # img.close()
    # plot_url = base64.b64encode(img.getvalue())
    
    return render_template('prediction.html',results=results, url=plot_data)

if __name__=='__main__':
    app.run(debug=True)