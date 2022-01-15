import matplotlib.pylab as plt

MODEL_COLUMN = ['%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']
PROJECTION_COLUMNS = ['production_', 'self_consumption_level']
MODEL_NAME = ['energy_production_model.pkl',
              'energy_self_consumption_model.pkl',
]

def standarize_data(scaler, X, fit =False, MODEL_COLUMN=MODEL_COLUMN):
    sel_left_range = 3
    keep_column, sel_column = MODEL_COLUMN[:sel_left_range], MODEL_COLUMN[sel_left_range:]
    if fit:
        scaler.fit(X[sel_column])
    temp = scaler.transform(X[sel_column])
    output_X = X[keep_column]
    output_X.loc[:, sel_column] = temp
    return output_X

def projection_refactor(df):
    df['self_consumption_'] = df['production_'] * df['self_consumption_level']
    df.drop('self_consumption_level', axis='columns', inplace=True)

def savings_df_report(df, source_name = '', kWh_cost=0.6, export_back = 0.8, curr = 'PLN'):
    prod = df['production_'].sum()
    self_cons = df['self_consumption_'].sum()
    savings_kWh = (prod - self_cons) * export_back + self_cons
    savings_curr = savings_kWh * kWh_cost
    return """{}
        ---------------------------------------------
        production              :{:10,.2f}
        self consumption        :{:10,.2f}
        self consumption level  :{:10,.2%}
        savings                 :{:10,.2f} kWh
                                :{:10,.2f} {}
                            """.format(source_name, prod, self_cons, self_cons / prod, savings_kWh, savings_curr, curr)



def projection_in_graph(monthly_energy_df, projection_df, filename = '', ax=None):
    if filename: plt.ioff()
    if not ax:
        _, ax = plt.subplots(figsize=(6, 3), dpi=200)
    ax.set_title('Real and Projection Report', fontsize="x-small")
    ax.plot(monthly_energy_df['month_str'], monthly_energy_df['production_'], label = 'production real ', color='blue')
    ax.plot(projection_df['month_str'], projection_df['production_'], label = 'production pred ', color='orange')
    ax.plot(monthly_energy_df['month_str'], monthly_energy_df['self_consumption_'], label = 'self consumption real ', color='blue', ls="dashed" )
    ax.plot(projection_df['month_str'], projection_df['self_consumption_'], label = 'self consumption pred ', color='orange', ls="dashed", alpha=0.5 )
    plt.xticks(rotation=90, fontsize="xx-small")
    plt.yticks(fontsize="xx-small")
    plt.legend(loc="upper center", fontsize="xx-small")
    ax.grid(ls=':')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    return plt