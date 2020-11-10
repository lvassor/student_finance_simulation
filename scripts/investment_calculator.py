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
from matplotlib.figure import Figure
from io import StringIO, BytesIO
import base64
from PIL import Image

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
    time = TextField("Time (years)")
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

@app.route('/prediction')
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
    
    fig = plt.figure()
    # Define colors
    colors = ((223/255, 221/255, 221/255), (0.298, 0.686, 0.314))
    cmap = LinearSegmentedColormap.from_list('Custom', colors, len(colors))
    ax = sns.heatmap(binary,linewidths=0.3, linecolor='#041A32', cmap=cmap)
    ax.set_xlabel("Monthly deposit", color="white")
    ax.set_ylabel("Principal", color="white")
    sns.despine()
    ax.spines['bottom'].set_linewidth(1)
    ax.spines['bottom'].set_color('#041A32')
    ax.spines['left'].set_linewidth(1)
    ax.spines['left'].set_color('#041A32')

    ax.tick_params(axis='y', which='both', colors='white', width=5)
    ax.tick_params(axis='x', which='both', colors='white', width=5)

    # Set the colorbar labels
    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks([0.25,0.75])
    colorbar.set_ticklabels(['Miss target', 'Meet target'])
    colorbar.ax.tick_params(colors="white")
    plt.ylim(11,0)
    plt.tight_layout()
    fig.patch.set_facecolor('#041A32')
    # Convert plot to img 
    # plt.savefig(output, format='png',dpi=100, facecolor='#041A32', bbox_inches='tight')
    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)

    # Encode PNG to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('ascii')
    pngImage.seek(0)
    
    
    return render_template('prediction.html',results=results, image=pngImageB64String)

if __name__=='__main__':
    app.run(debug=True)