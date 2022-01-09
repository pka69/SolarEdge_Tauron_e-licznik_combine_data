import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
        filter_list = set(df[filter])  
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
        group_df = df.groupby(group_by)[series_to_plot].agg(agg) if group_by else df
        if mean:
            group_df['mean'] = np.mean(group_df[series_to_plot])
            series_to_plot += 'mean'
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
            group_df.index,
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
    ax.grid(True)
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
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
            group_df.index,
            group_df[item] * multiply, 
            width = 1.0, 
            bottom=True, 
            color = colors[idx] if colors else STD_COLORRANGE[idx],
            label= item.replace('_', ' '),
            histtype='step', 
            alpha = 0.4,
        )
    ax.grid(True)
    ax.legend(fontsize='xx-small',  loc='upper left')  # bbox_to_anchor=(1.05, 0.9),
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    plt.show()
    return group_df
    
def lineplot(
    df, group_by, series_to_plot, 
    colors=[], 
    fill = [], 
    agg='sum', 
    filename='lineplot.png', 
    filter='', 
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
        ax.plot(
            group_df.index,
            group_df[item] * multiply,  
            color = colors[idx] if colors else STD_COLORRANGE[idx],
            label= item.replace('_', ' '),
        )
        if item in fill:
            ax.fill_between(
                group_df.index,
                group_df[item], 
                alpha = 0.3,
            )
    ax.grid(True)
    ax.legend(fontsize='xx-small',  loc='upper left')  # bbox_to_anchor=(1.05, 0.9),
    ax.tick_params(axis='both', which='major', labelsize="xx-small")
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(unit,fontsize='xx-small')
    ax.set_xlabel(group_by,fontsize='xx-small')
    if filename:
        plt.savefig('{}.png'.format(filename), bbox_inches='tight')
    plt.show()
    return group_df