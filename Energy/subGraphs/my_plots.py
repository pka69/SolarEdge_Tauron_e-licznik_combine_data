import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .my_graph_speedo import speedometer

STD_COLORRANGE = ['blue', 'orange', 'green', 'gray', 'yellow']

def simple_data_preparation(
    df, 
    group_by, 
    series_to_plot, 
    colors=[], 
    fill = [], 
    agg='sum', 
    filter='', 
    unit='', 
    multipliy=1,
    mean=False,
):
    new_fill = fill
    new_colors = colors
    if filter:
        filter_list = set(df[filter[0]])  
        group_df = pd.DataFrame()
        new_fill = []
        new_colors = []
        for series in series_to_plot:
            for idx, item in enumerate(filter_list):
                temp_df = df[df[filter]==item].groupby(group_by)[series_to_plot].agg(agg) if group_by else df[df[filter]==item]
            
                temp_df.rename(columns={series: item + "-" + series}, inplace=True)
                new_colors.append(colors[idx] if colors else STD_COLORRANGE[idx])
                # group_df = group_df.append(temp_df, ignore_index=False)
                group_df = group_df.join(temp_df, how='outer')
            for series in fill:
                new_fill.append(item + "-" + series)
            if mean:
                mean_column = [col for col in group_df.columns if col.endswith("-" + series)]
                group_df[ "mean-" + series] = np.mean(group_df[mean_column], axis=1)
                new_colors.append('black')
            for idx, item in enumerate(filter_list):
                group_df[item + "-" + series + "%"] = group_df[item + "-" + series] / group_df["mean-" + series] * 100
        series_to_plot = [col for col in group_df.columns if not col.endswith("%")]
    else:
        group_df = df.groupby(group_by)[series_to_plot].agg(agg).reset_index() if group_by else df
        if mean:
            # group_df['mean'] = np.mean(group_df[series_to_plot])
            # series_to_plot += 'mean'
            mean_df = df.groupby(group_by)[series_to_plot].mean().reset_index()
            for col in mean_df.columns[1:]:
                mean_df.rename(columns = {col: "mean_" + col}, inplace=True )
            
            group_df = pd.merge(left=group_df, right=mean_df, on=group_by )
            series_to_plot += mean_df.columns[1:].tolist()
    return group_df, series_to_plot, new_colors, new_fill

def barplot(
    df, group_by, series_to_plot,  # df to plot, column to group data, # column to show on plot
    colors=[],  # colors to use on graph
    agg='sum', 
    filename='barplot.png', 
    filter='', 
    fill=[], 
    unit='', 
    multiply=1, 
    mean=False, 
    ax=None
):
    if not ax:
        fig, ax = plt.subplots(figsize=(8,4), dpi=200)
        fig.tight_layout()
    group_df, series_to_plot, colors, fill  = simple_data_preparation(
        df=df, 
        group_by=group_by, 
        series_to_plot=series_to_plot, 
        colors=colors, 
        fill=fill, 
        agg=agg, 
        filter=filter, 
        mean=mean
    )
    for idx, item in enumerate(series_to_plot):
        ax.bar(
            group_df[group_by],
            group_df[item] * multiply, 
            width = 1.0, 
            bottom=True, 
            color = colors[idx] if colors else STD_COLORRANGE[idx],
            label= item.replace('_', ' '),
            edgecolor = 'gray', 
            alpha = 0.4,
        )
    ax.legend(fontsize='xx-small',  loc='upper left')  # bbox_to_anchor=(1.05, 0.9),
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    ax.tick_params(axis='x', rotation=90)
    ax.grid(True, ls=":")
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    else:
        plt.show()
    return group_df

def histplot(
    df, group_by, series_to_plot, 
    colors=[], 
    agg='sum', 
    filename='histplot.png', 
    filter='', 
    fill=[], 
    unit='', 
    multiply=1, 
    mean=False, 
    ax=None
):
    if not ax:
        fig, ax = plt.subplots(figsize=(8,4), dpi=200)
        fig.tight_layout()
    group_df, series_to_plot, colors, fill  = simple_data_preparation(
        df=df, 
        group_by=group_by, 
        series_to_plot=series_to_plot, 
        colors=colors, 
        fill=fill, 
        agg=agg, 
        filter=filter, 
        mean=mean
    )
    for idx, item in enumerate(series_to_plot):
        ax.hist(
            group_df[group_by],
            group_df[item] * multiply, 
            width = 1.0, 
            bottom=True, 
            color = colors[idx] if colors else STD_COLORRANGE[idx],
            label= item.replace('_', ' '),
            histtype='step', 
            alpha = 0.4,
        )
    
    ax.grid(True, ls=":")
    ax.legend(fontsize='xx-small',  loc='upper left')  # bbox_to_anchor=(1.05, 0.9),
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    else:
        plt.show()
    return 
    
def lineplot(
    df, group_by, series_to_plot, 
    colors=[], 
    fill = [], 
    fill_between={},
    agg='sum', 
    filename='lineplot.png', 
    filter='', 
    unit='',
    multiply=1,
    mean=False,
    title='',
    ax=None,
    figsize=(8,4),
):
    own_ax = False
    if not ax:
        fig, ax = plt.subplots(figsize=figsize, dpi=200)
        fig.tight_layout()
        ax.set_title(title, fontsize='x-small')
        own_ax = True
        
    group_df, series_to_plot, colors, fill  = simple_data_preparation(
        df=df, 
        group_by=group_by, 
        series_to_plot=series_to_plot, 
        colors=colors, 
        fill=fill, 
        agg=agg, 
        filter=filter, 
        mean=mean
    )
    for item in fill_between.keys():
        ax.fill_between(
            group_df[group_by],
            group_df[fill_between[item][0]], 
            group_df[fill_between[item][1]], 
            label= item.replace('_', ' '),
            alpha = 0.3,
        )
    for idx, item in enumerate(series_to_plot):
        ax.plot(
            group_df[group_by],
            group_df[item] * multiply,  
            color = colors[idx] if colors else STD_COLORRANGE[idx],
            label= item.replace('_', ' '), ls="-" if item.find("mean")==-1 else ":"
        )
        if item in fill:
            ax.fill_between(
                group_df[group_by],
                group_df[item], 
                alpha = 0.3,
            )
    
    ax.grid(True)
    ax.legend(fontsize='xx-small',  loc='upper left')  # bbox_to_anchor=(1.05, 0.9),
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if own_ax:
        if filename:
            plt.savefig('{}.png'.format(filename), bbox_inches='tight')
        else:
            plt.show()
    return 

def set_of_speedo(stat_df, filename=''):
    no_of_measures = stat_df['mean'].count()
    weight, hight = 6, 5 / no_of_measures
    columns = stat_df['index'].tolist()
    min_value = stat_df['min'].tolist()
    max_value = stat_df['max'].tolist()
    speedo_value = stat_df['mean'].tolist()
    if filename: plt.ioff()
    fig, ax = plt.subplots(1,no_of_measures,figsize = (weight, hight), dpi=200)
    fig.tight_layout()
    for idx, col in enumerate(columns):
        ax[idx].xaxis.label.set_size(3)
        ax[idx].yaxis.label.set_size(3)
        ax[idx].tick_params('both', )
        ax[idx].axis('off')
        # ax[idx].set_title(" " + col.replace("_", " "), fontsize=5)
        speedometer(
            ax[idx],
            min_value[idx], max_value[idx], speedo_value[idx],
            title=" " + col.replace("_", " "),
            unit='kWh', 
            start_angle=0, end_angle=180,
            title_fontsize=5, label_fontsize=3,
            annotation_fontsize=5, 
            annotation_facecolor='gray', 
            annotation_edgecolor="lightgray",
            annotation_offset=0.6, annotation_pad=0.5,
            fade_alpha=0.9,
        )
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    else:
        plt.show()
    return


def swarmplot(
    df, group_by, series_to_plot, 
    colors=[], 
    fill = [], 
    fill_between={},
    agg='sum', 
    filename='lineplot.png', 
    filter='', 
    unit='',
    multiply=1,
    mean=False,
    title='',
    ax=None,
    dotsize=2,
    figsize=(8,4),
):
    own_ax = False
    if not ax:
        fig, ax = plt.subplots(figsize=figsize, dpi=200)
        # fig.tight_layout()
        ax.set_title(title, fontsize='x-small')
        own_ax = True
    group_df, series_to_plot, colors, fill  = simple_data_preparation(
        df=df, 
        group_by=group_by, 
        series_to_plot=series_to_plot, 
        colors=colors, 
        fill=fill, 
        agg=agg, 
        filter=filter, 
    )
    df = pd.DataFrame()
    for col in series_to_plot:
        temp_df = group_df[[group_by, col]].rename(columns={col: 'value'})
        temp_df['category'] = np.array([col.replace("_", " ")] * len(group_df.index.to_list()))
        df = pd.concat([df, temp_df])
    sns.set_theme(style="whitegrid", palette="muted")
    sns.swarmplot(data=df, x="value",  y="category", s=dotsize, ax=ax) # orient='v'
    ax.set_ylabel("", fontsize="xx-small")
    ax.set_xlabel(unit, fontsize="xx-small")
    ax.legend(fontsize='xx-small',  loc='best')
    ax.grid(True)
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    if own_ax:
        if filename:
            plt.savefig('{}.png'.format(filename), bbox_inches='tight')
        else:
            plt.show()
    return 
    
    

    
