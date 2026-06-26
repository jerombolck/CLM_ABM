import numpy as np

def compute_layers_score(ray_lengths, isovist):
    # Only foreground: 2
    # Only foreground and middleground: 4
    # fore- middle and background: 6
    # cluttered? Penalty of max. 2
    n_rays = len(ray_lengths)

    foreground_rays = [x for x in ray_lengths if x < 100]
    middleground_rays = [x for x in ray_lengths if x > 100 and x < 400]
    background_rays = [x for x in ray_lengths if x > 400]

    n_foreground_rays = len(foreground_rays)
    n_middleground_rays = len(middleground_rays)
    n_background_rays = len(background_rays)

    has_foreground = n_foreground_rays / n_rays > 0.05
    has_middleground = n_middleground_rays / n_rays > 0.05
    has_background = n_background_rays / n_rays > 0.05

    normalized_stds = []

    if has_foreground:
        max_std = 100 / 2
        normalized_stds.append(np.std(foreground_rays)/max_std)
    if has_middleground:
        max_std = (400 - 100) / 2
        normalized_stds.append(np.std(middleground_rays)/max_std)
    if has_background:
        max_std = (500 - 400) / 2
        normalized_stds.append(np.std(background_rays)/max_std)

    if len(normalized_stds) == 0:
        return 1
    
    mean_normalized_std = 1 - np.mean(normalized_stds)   

    if has_foreground and has_background and has_middleground:
        layers_score = 1 + mean_normalized_std * 5
    else:
        layers_score = 1 + mean_normalized_std * 3

    return layers_score


def test(ls):
    print(1-(np.std(ls)/360*2))


lists = [
    [100, 120, 140],
    [20, 300, 40],
    [0, 180, 180],
    [0, 0, 360]
]

for l in lists:
    test(l)

