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

    normalized_stds = []

    if has_foreground:
        max_std = foreground_dist / 2
        normalized_stds.append(np.std(foreground_rays)/max_std)
    if has_middleground:
        max_std = (background_dist - foreground_dist) / 2
        normalized_stds.append(np.std(middleground_rays)/max_std)
    if has_background:
        max_std = (500 - background_dist) / 2
        normalized_stds.append(np.std(background_rays)/max_std)

    if len(normalized_stds) == 0:
        return 1
    
    mean_normalized_std = np.clip(1 - np.mean(normalized_stds), 0, 1)

    if has_foreground and has_background and has_middleground:
        layers_score = mean_normalized_std * 7
    else:
        layers_score = mean_normalized_std * 4

    return layers_score
