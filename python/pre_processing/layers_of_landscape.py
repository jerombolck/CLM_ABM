import numpy as np

def compute_layers_score(ray_lengths, foreground_dist = 200 , background_dist = 400):
    n_rays = len(ray_lengths)

    foreground_rays = [x for x in ray_lengths if x <= foreground_dist]
    middleground_rays = [x for x in ray_lengths if x > foreground_dist and x < background_dist]
    background_rays = [x for x in ray_lengths if x >= background_dist]

    n_foreground_rays = len(foreground_rays)
    n_middleground_rays = len(middleground_rays)
    n_background_rays = len(background_rays)

    has_foreground = n_foreground_rays / n_rays > 0.05
    has_middleground = n_middleground_rays / n_rays > 0.05
    has_background = n_background_rays / n_rays > 0.05

    layers_present = has_background + has_middleground + has_foreground

    if layers_present == 2 and not has_background:
        layers_score = 2
    elif (layers_present == 2 and has_background) or (layers_present == 3 and not has_background):
        layers_score = 4
    elif layers_present == 3 and has_background:
        layers_score = 6
    else:
        layers_score = 1

    return layers_score
