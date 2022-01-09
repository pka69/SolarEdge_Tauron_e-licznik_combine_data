from copy import deepcopy
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Wedge, Rectangle
from matplotlib import cm
import matplotlib.patheffects as path_effects


DAL = {  #  DEFAULT_ARG_LIST
    'radius': 4,
    'width_ratio': 1/4,
    'colors': ["#d7191c", "#fdae61", "#ffffbf", "#abd9e9", "#2c7bb6"],
    'midpoint_values': None, 
    'segments_per_color': 5,
    'start_angle': -30,
    'end_angle': 210,
    'arc_edgecolor': None,
    'fade_alpha': 0.25,
    'patch_lw': 0.25,
    'snap_to_pos': False,
    'title': '',
    'unit': '',
    'label_fontsize': 7,
    'label_fontcolor': mpl.rcParams['axes.labelcolor'],
    'title_fontcolor': mpl.rcParams['axes.labelcolor'],
    'title_facecolor': None,
    'title_edgecolor': None,
    'title_offset': 1.5,
    'title_pad': 1,
    'title_fontsize': 18,
    'draw_annotation': True,
    'annotation_text': None,
    'annotation_fontcolor': mpl.rcParams['axes.labelcolor'],
    'annotation_facecolor': None,
    'annotation_edgecolor': None,
    'annotation_offset': 0.75,
    'annotation_pad': 0,
    'annotation_fontsize': 16,
    'draw_labels': True,
    'labels': None,
    'range_labels': None,
    'range_label_fontsize': 5,
    'rotate_labels': False,
    'fade_hatch': None,
    'center': (0, 0),
    'border': False,
    'border_color':'b',
    'border_thickness': 1,
    'reverse': False,
}

def degree_range(edge_values, start=0, end=180):
    """
    returns a tuple of an Nx2 array of start and end angles
    and the midpoints of each of those ranges
    """
    end_ =  np.array([(start + (i - edge_values[0])/(edge_values[-1] -edge_values[0]) * (end - start)) for i in edge_values[:-1]]) 
    # np.linspace(start, end, n+1, endpoint=True)[0:-1]
    start_ =   np.array([(start + (i - edge_values[0])/(edge_values[-1] -edge_values[0]) * (end - start)) for i in edge_values[1:]]) 
    # np.linspace(start, end, n+1, endpoint=True)[1::]
    mid_points = end_ + ((end_-start_)/2.)
    return np.c_[start_, end_], mid_points


def rotate(angle):
    rotation = np.degrees(np.radians(angle) * np.pi / np.pi - np.radians(90))
    return rotation

def set_annotation_text(local_DAL, value):
    if local_DAL['annotation_text'] is None:
            local_DAL['annotation_text'] = f'{value} {local_DAL["unit"]}'

def update_DAL(ax, local_DAL):
    if local_DAL['arc_edgecolor'] is None:
            local_DAL['arc_edgecolor'] = ax.get_facecolor()
    if local_DAL['title_facecolor'] is None:
            local_DAL['title_facecolor'] = ax.get_facecolor()  
    if local_DAL['title_edgecolor'] is None:
            local_DAL['title_edgecolor'] = ax.get_facecolor()
    if local_DAL['annotation_facecolor'] is None:
            local_DAL['annotation_facecolor'] = ax.get_facecolor()
    if local_DAL['annotation_edgecolor'] is None:
            local_DAL['annotation_edgecolor'] = ax.get_facecolor()

def speedometer(
    ax,
    start_value, 
    end_value,
    value, 
    **kwargs
):
    def set_arrow_angle():
        if local_DAL['snap_to_pos']:
            arrow_angle = midpoints[-1::-1][(arrow_index - len(colors))]
        else:
            deg_range = local_DAL['end_angle'] - local_DAL['start_angle']
            val_range = end_value - start_value
            arrow_angle = local_DAL['start_angle'] + (value - start_value) / val_range * deg_range
        return arrow_angle
    
    local_DAL =deepcopy(DAL)
    for key, val in kwargs.items():
        if key in local_DAL.keys():
            local_DAL[key] = val
        else:
            raise ValueError("no '{}' on avaliable param list".format(key))
    local_DAL['start_angle'] = 180 - local_DAL['start_angle']
    local_DAL['end_angle'] = 180 - local_DAL['end_angle']
    update_DAL(ax, local_DAL)
    n_colors = len(local_DAL['colors'])
    if local_DAL['segments_per_color']:
        colors = np.repeat(local_DAL['colors'], local_DAL['segments_per_color'])
        midpoint_values = np.linspace(start_value, end_value, local_DAL['segments_per_color']*n_colors, endpoint=True)
        edge_values = np.linspace(start_value, end_value, local_DAL['segments_per_color']*n_colors+1, endpoint=True)
        arrow_index = np.argmin(abs(midpoint_values - value))
    else:
        local_DAL['segments_per_color'] = 1
        colors = local_DAL['colors']
        midpoint_values = []
        edge_values = local_DAL['midpoint_values']
        for idx in range(1, len(edge_values)):
            midpoint_values.append((edge_values[idx] + edge_values[idx-1])/2)
        arrow_index = np.argmin(abs(min(midpoint_values) - value))
        if local_DAL['labels'] is None:
            local_DAL['labels'] = ['' for i in range(len(colors)+1)]
            for i, l in zip(range(0, n_colors+1),
                            edge_values):
                local_DAL['labels'][i] = l
    arrow_value = midpoint_values[arrow_index]
    
    if local_DAL['labels'] is None:
        local_DAL['labels'] = ['' for i in range(len(colors)+1)]
        for i, l in zip(range(0, local_DAL['segments_per_color']*n_colors+1, local_DAL['segments_per_color']),
                        np.linspace(start_value, end_value, n_colors+1, endpoint=True)):
            local_DAL['labels'][i] = l

    N = len(colors)
    angle_range, midpoints = degree_range(edge_values, start=local_DAL['start_angle'], end=local_DAL['end_angle'])
    annotation_angles = np.concatenate([angle_range[:, 1], angle_range[-1:, 0]])
    patches = []
    for ang, c, val in zip(angle_range, colors, edge_values[-2::-1]): # self.midpoint_values[-1::-1]
        if arrow_value <= val:
            alpha = local_DAL['fade_alpha']
            hatch = local_DAL['fade_hatch']
        else:
            alpha = 1
            hatch = None
        # Wedges
        patches.append(Wedge(local_DAL['center'], local_DAL['radius'], *ang, width=local_DAL['width_ratio']*local_DAL['radius'],
            facecolor=c, edgecolor=local_DAL['arc_edgecolor'], lw=local_DAL['patch_lw'], alpha=alpha, hatch=hatch))
        # Wedges with just an edgecolor (alpha edgecolor issues)
        patches.append(Wedge(local_DAL['center'], local_DAL['radius'], *ang, width=local_DAL['width_ratio']*local_DAL['radius'], facecolor='None', edgecolor=local_DAL['arc_edgecolor'], lw=local_DAL['patch_lw']))
        # print("ang:" , ang,
        #       "color:", c,
        #       "edge_values:", val,
        #       )
    [ax.add_patch(p) for p in patches]
    
    if local_DAL['draw_labels']:
        for angle, label in zip(annotation_angles, local_DAL['labels']):
            # print(
            #         "angle:", angle,
            #         "label:", label
            #     )
            if local_DAL['rotate_labels']:
                radius_factor = 0.625
                adj = -90
                # if angle < 90:
                #     adj = 90
                # else:
                #     adj = -90
            else:
                radius_factor = 0.65
                if (angle < 0) | (angle > 180):
                    adj = 180
                else:
                    adj = 0

            if type(label) == str:
                if label[-2:] == '.0':
                    label = label[:-2]

            ax.text(local_DAL['center'][0] + radius_factor * local_DAL['radius'] * np.cos(np.radians(angle)),
                local_DAL['center'][1] + radius_factor * local_DAL['radius'] * np.sin(np.radians(angle)),
                label, horizontalalignment='center', verticalalignment='center', fontsize=local_DAL['label_fontsize'],
                fontweight='bold', 
                color=local_DAL['label_fontcolor'], 
                rotation=rotate(angle) + adj,
                # bbox={'facecolor': local_DAL['arc_edgecolor'], 
                #       'ec': 'None', 'pad': 0},
                zorder=10)
        if local_DAL['range_labels']:
            # annotation_angles = [(annotation_angles[i]+annotation_angles[i+1])/2 for i in range(len(annotation_angles)-1) ]
            # for angle, label in zip(annotation_angles, local_DAL['range_labels']):
            #     # print(
            #     #     "angle:", angle,
            #     #     "label:", label
            #     # )
            #     if local_DAL['rotate_labels']:
            #         radius_factor = 0.85
            #         adj = -90
            #         # if angle < 90:
            #         #     adj = 90
            #         # else:
            #         #     adj = -90
            #     else:
            #         radius_factor = 0.85
            #         if (angle < 0) | (angle > 180):
            #             adj = 180
            #         else:
            #             adj = 0
                # text = ax.text(local_DAL['center'][0] + radius_factor * local_DAL['radius'] * np.cos(np.radians(angle)),  
                #     local_DAL['center'][1] + radius_factor * local_DAL['radius'] * np.sin(np.radians(angle)), 
                #     label, horizontalalignment='center', verticalalignment='center', fontsize=local_DAL['range_label_fontsize'],
                #     fontweight='light', color=local_DAL['label_fontcolor'], rotation=rotate(angle) + adj,
                #     # bbox={'facecolor': local_DAL['arc_edgecolor'], 'ec': 'None', 'pad': 0},
                #     zorder=10)
                # text.set_path_effects([path_effects.withStroke(linewidth=0.5, foreground='w')])
            # print(
            #     'angle1: ', annotation_angles[:-1],
            #     'angle2: ', annotation_angles[1:],
            #     'label:', local_DAL['range_labels']
            # )
            for angle1, angle2, label in zip(annotation_angles[:-1], annotation_angles[1:], local_DAL['range_labels']):
                adj = 0
                radius_factor = 0.85
                # if local_DAL['rotate_labels']:
                #     radius_factor = 0.85
                #     adj = -90
                # else:
                #     radius_factor = 0.85
                #     if (angle1 < 0) | (angle1 > 180):
                #         adj = 180
                #     else:
                #         adj = 0
                steps = len(label) + 1
                angle_step = (angle2-angle1) / steps
                for idx in range(len(label)):
                    letter = label[idx]
                    angle = angle1 + (idx+1) * angle_step
                    text = ax.text(
                        local_DAL['center'][0] + radius_factor * local_DAL['radius'] * np.cos(np.radians(angle)),  
                        local_DAL['center'][1] + radius_factor * local_DAL['radius'] * np.sin(np.radians(angle)), 
                        letter, 
                        horizontalalignment='center', 
                        verticalalignment='center', 
                        fontsize=local_DAL['range_label_fontsize'],
                        fontweight='light', 
                        color=local_DAL['label_fontcolor'], 
                        rotation=rotate(angle) + adj,
                        # bbox={'facecolor': local_DAL['arc_edgecolor'], 'ec': 'None', 'pad': 0},
                        zorder=10)
                    # text.set_path_effects([path_effects.withStroke(linewidth=0.5, foreground='w')])
                    
    arrow_angle = set_arrow_angle() 
    
    ax.arrow(
        *local_DAL['center'],
        .525 * local_DAL['radius'] * np.cos(np.radians(arrow_angle)),
        .525 * local_DAL['radius'] * np.sin(np.radians(arrow_angle)),
        width=local_DAL['radius']/25, 
        head_width=local_DAL['radius']/10, 
        head_length=local_DAL['radius']/15,
        fc=ax.get_facecolor(), 
        ec=local_DAL['label_fontcolor'], 
        zorder=9, 
        # alpha=0.5,
        lw=1)
# arrow center
    ax.add_patch(Circle(
        local_DAL['center'], 
        radius=local_DAL['radius']/30, 
        fc=ax.get_facecolor(), 
        edgecolor=local_DAL['label_fontcolor'],  
        lw=1., 
        # alpha=0.5,
        zorder=10))

    set_annotation_text(local_DAL, value)

    annotation = ax.text(local_DAL['center'][0], local_DAL['center'][1] - local_DAL['annotation_offset'] * local_DAL['radius'], 
        local_DAL['annotation_text'], horizontalalignment='center',
        verticalalignment='center', fontsize=local_DAL['annotation_fontsize'], fontweight='bold', color=local_DAL['annotation_fontcolor'],
        bbox={
            'boxstyle': 'square, pad=0.3',
            'facecolor': local_DAL['annotation_facecolor'], 
            'edgecolor': local_DAL['annotation_edgecolor'], 
            'pad': local_DAL['annotation_pad']},
        zorder=11, visible=False)

    if local_DAL['draw_annotation']:
        annotation.set_visible(True)

    # Title Annotation
    if local_DAL['title']:
        ax.text(local_DAL['center'][0], local_DAL['center'][1] + local_DAL['title_offset'] * local_DAL['radius'], 
            local_DAL['title'], horizontalalignment='center',
            verticalalignment='center', fontsize=local_DAL['title_fontsize'], fontweight='bold', 
            color=local_DAL['title_fontcolor'],
            bbox={'facecolor': local_DAL['title_facecolor'], 'edgecolor': local_DAL['title_edgecolor'], 'pad': local_DAL['title_pad']},
            zorder=11)
  
    if local_DAL['border']:
        autoAxis = ax.axis()
        rec = Rectangle((autoAxis[0]-0.7,autoAxis[2]-0.2),(autoAxis[1]-autoAxis[0])+1,(autoAxis[3]-autoAxis[2])+0.4,
                        fill=False,
                        lw=local_DAL['border_thickness'],
                        color=local_DAL['border_color'])
        rec = ax.add_patch(rec)
        rec.set_clip_on(False)

if __name__ == "__main__":
    test_data = [
            [40, 59.9, 81, 90.7, 103.7, 120],
            ['Niedowaga', 'W normie', 'Nadwaga', 'Otyłość I', 'Otyłość II'],
            ['lightblue', '#00CC00', 'yellow', 'orange', 'red'],
        ]
    fig, ax = plt.subplots(1,2,figsize = (5,2), dpi=200)

    speedometer(ax[0], 0, 100, 75, fade_alpha = 1, 
                unit='m/s',
                start_angle=-90,
                end_angle=180,
                annotation_fontsize=10,
                annotation_facecolor='gray', 
                annotation_edgecolor="black",
                # title_pad=2,
    )
    ax[0].axis('off')
    speedometer(ax[1], 40, 120, 100, 
                segments_per_color=0, 
                colors = test_data[2], 
                range_labels = test_data[1], 
                midpoint_values=test_data[0], 
                fade_alpha = 1,
                title="Waga",
                unit='kg',
                annotation_fontsize=10,
                start_angle=-0,
                end_angle=210,
                annotation_facecolor='lightgray', 
                annotation_pad=0.5,
                annotation_offset=0.6,
                # annotation_edgecolor="b",
                # reverse=True,
                )
    ax[1].axis('off')
    ax[1].set_title('Waga')
    plt.savefig("testowanie.png")
    plt.show()
