# Exploring the Potential of Open Geodata and Agent Based Modelling for Evaluating Urban Contemplative Landscapes

**Agent-based model (ABM) developed as part of a master's thesis project by Jerom Bolck**

In this README the ABM that is contained within this repository is summarized following the ODD protocol (Grimm et al., 2020) for the purpose of documentation. It it not intended to be a replacement of the main thesis report which more thoroughly explains the design decisions that were made.

## Disclaimer
This repository has been prepared by a student of Wageningen University as part of a master's programme and under the supervision of the Laboratory of Geo-information Science and Remote Sensing. It is not an official publication of Wageningen University & Research (WUR), and its contents do not necessarily reflect the views or opinions of WUR.

The use of code contained in this repository is at the user's own risk.

Wageningen University & Research accepts no liability for any consequences arising from the use of code contained in this repository.

## Purpose and Patterns
The purpose of this model is to explore the potential of using agent-based modelling and open geodata for integrating mental health considerations in urban planning. It serves as an exploration of the methodology to operationalise mental health and environmental psychology theory into model parameters and generate useful insights using agent-based modelling.

This model specifically aims to simulate the exposure of residents of Overvecht to elements in the urban environment that can contribute to positive mental health, according to the Contemplative Landscape Model (CLM) (Olszewska-Guizzo et al., 2022). It explores the spatial distribution of these elements, and how the daily routine of residents impacts their exposure to these elements throughout a typical day. 

## Entities, State Variables and Scales
### Entities
The agents of this model are referred to as residents. They represent urban residents that are living and working in Overvecht. Each resident has the following state variables:

- **Group:** the resident group that the resident belongs to,
- **Home node:** the network node representing the resident’s home location.
- **Work node:** the network node representing the resident’s workplace.
- **Current destination:** the network node the agent is currently travelling toward, if any.
- **Current goal:** the current task in the resident’s daily schedule (e.g. travelling to work, returning home).
- **Current path:** an ordered list of network nodes that represents the resident’s route from their last node to the current destination.
- **‘Moving?’ flag:** a boolean that indicates whether the resident is currently moving.
- **CLM exposure scores:** a list of momentary exposure scores per CLM component, recorded at each tick during movement
- **Total CLM score:** a list of momentary exposure scores, average of all CLM component scores, recorded at each tick during movement

Resident belong to different resident groups, as specified in “data/model_input/resident_groups.csv”.

Their resident group determines their daily routine. Resident groups have the following state variables:

- **Group name:** the name of the resident group.
- **Group proportion:** the proportion of all residents that belong to this group.
- **Work start hour:** the mean of the time at which residents of this group go to work.
- **Work start spread:** the standard deviation of the time at which residents of this group go to work.
- **Work end hour:** The mean of the time at which residents of this group leave work.
- **Work end spread:** The standard deviation of the time at which residents of this group leave work.
- **Shop probability:** The probability that a resident of this group goes to a shop after work.
- **Shop duration:** The time that residents of this group spends at a shop.
- **Shop end spread:** The standard deviation of the time at which resisidents of this group leave a shop.

The street network is a vector-based network of nodes and edges built from GIS street data. It represents the streets that residents can walk and bike on. The network is only structural and has no state variables.

Home locations, work locations and shop locations are point vectors that describe the places that residents travel between. They represent resident homes, their workplaces, and shops they can visit respectively. These locations do not have state variables and do not change when the model is running. Sample points are also static point vectors. They are located at a regular 50 meter interval along all network edges. All sample points have score values for each CLM component and an overall CLM score.

### Scales
- **Spatial extent:** the model covers the neighbourhood of Overvecht in Utrecht, the Netherlands, which is around 8.5 km².
- **Spatial resolution:** 1 meter corresponds to 0.199 NetLogo units
- **Temporal resolution:** one time step represents one minute

## Process Overview and Scheduling
All processes happen on an agent level. There are no environmental level processes in the model. Each time step the following steps are executed (see also the figure below):

1. **Advance time:** Simulated time is advanced by one minute. Any agent who has reached their current goal’s end time is asked to schedule a new goal and determine a new destination according this new goal.
2. **Move residents:** Residents that are currently moving to a destination are moved along  their current path. How far they move along their path depends on their speed. The speed determines the distance travelled per time step. Residents continue to advance towards the next node in their path until they have covered this distance.
3. **Record exposure:** Moving residents record the CLM (component) scores of their nearet sample point.

<img width="652" height="490" alt="image" src="https://github.com/user-attachments/assets/59333dfb-be04-4fda-a9dc-abf1e576b842" />


## Design Concepts
The model is based on the CLM and adapts the three-layer structure and the daily routines of agents from the framework by Yang et al. (2018). The three-layer structure was itself adapted from Leyk et al. (2009) and is adapted again for this thesis (see figure below). Selected components of the CLM are operationalized using GIS data and used as the main input features of the model.

<img width="621" height="193" alt="image" src="https://github.com/user-attachments/assets/9d8b1397-0705-4e8b-bd25-e6f2ffa433fe" />


### Emergence
The outcome of the model are the temporal and spatial patterns in CLM exposure. These patterns emerge from the combination of different daily routines, route choices, network layout, the spatial pattern of elements influencing CLM scores, and the spatial pattern of home and destination locations. Differences in CLM exposure between residents or days are therefore emergent properties of the model.

### Adaptation
Residents adapt their schedule one activity at a time. Once it is time for a scheduled activity, they start this activity, calculate the shortest path to the corresponding destination and at the scheduled end time they determine their next activity.

### Objectives, Learning and Prediction
Resident behaviour is completely determined by their daily schedule and neither past-experience or possible future scenarios are used in decision-making. Therefore, they do not optimise any objectives, do not learn and do not make any implicit or explicit predictions. 

### Sensing
For pathfinding purposes, residents are assumed to have perfect knowledge of the street network. For exposure purposes, residents record all CLM (component) scores  once during each time step. These scores are taken from the closest sample point to the resident’s location. They are precomputed in a GIS pipeline implemented in Python. Computation of the scores at runtime was not feasible within computational restrictions.

### Interaction
There is no interaction among residents in the model. It is assumed that their daily routines are not subject to change based on other resident’s behaviours.

### Stochasticity
Randomness is included in the model during initialization and when scheduling activities. During initialization, resident home and work nodes are selected randomly based on the available home and work locations.

When a resident schedules a new activity, the start time is based on a normal distribution, the mean and standard deviation of which are defined by a their resident group. This simulates a realistic variation in departure times between residents and across days.
The activity that is to be scheduled next depends on the current activity as well as on the shopping probability that is also defined by their resident group. If their new destination is to be a shop location, the shop location is also randomly selected from all shop locations.

### Collectives
Residents belong to resident groups. The attributes of their resident group determines their daily routine. Otherwise, resident groups are static and not affected by each other or by the residents.

### Observation
On an agent level, each resident stores a list of scores for each CLM component and the overall CLM score for every time step they were moving. At the population level, average scores per CLM component and overall are also recorded each time step.

Sample points record the number of times they were visited by a resident, incrementing this number every time a resident moves through it.

### Initialization
During initialization, the following setup steps take place:

#### Data loading
All spatial data is loaded from files that were pre-processed beforehand These files contain data for the overvecht street network, home, work and shop locations in overvecht, and sample points with CLM component scores. This data was reprojected to UTM zone 31N before importing in NetLogo, to be compatible with the GIS extension.
Homes, workplaces, and shop locations are added to the model from the loaded point features.

#### Network creation
A network is constructed using the NetLogo networks extension (NW). Line feautures from the loaded GIS data are loaded into the model. Their endpoints are added to the model as intersections (network nodes) which are then accordingly connected by streets (network edges).

#### Residents initialization
A starting number of residents, to be specified in the model interface, is created. Each resident is asigned a home node and a work node at random. They are placed at their home node at the start of the model. All residents schedule their first goal at the start of the model according to their daily routine. All residents will move with the same speed that is set in the model interface.

#### Input Data
All input data is obtained and pre-processed in a GIS pipeline using Python before running the model and is loaded during model initialization.

## Submodels 
### Scheduling
After a resident completes a goal, a new goal is scheduled. The figure below displays the logic behind this.

<img width="672" height="361" alt="image" src="https://github.com/user-attachments/assets/e8c05b0e-27ea-447e-a80b-151bbd403d08" />


### Path Calculation
Once a resident receives a new destination, a path is computed from their current intersection to their assigned destination intersection. Using the NW extension in Net Logo, the shortest path to the destination is found and the intersections on this path are assigned to the resident in order in a list.

### Movement
Residents that are not at their assigned destination will move towards it. The distance a resident travels in one timestep depends on the speed set during initialization.

Each timestep these residents advance along their assigned path until their reach their assigned destination. They proceed to the next intersection in their assigned path recursively. If the remaining distance the resident can travel in a timestep is more than the distance to the next intersection in their assigned path they move towards it and this intersection is removed from the path. This is repeated until the distance to the next intersection is larger the remaining distance the resident can travel. At this point the resident moves the remaining distance in the direction of the next node and the movement is concluded.

### CLM exposure
Residents that are moving will measure their exposure to the CLM components. During each time timestep, after the resident has finished moving, it locates the nearest CLM score sample point and records the scores of that sample point (see figure below).

<img width="739" height="260" alt="image" src="https://github.com/user-attachments/assets/fe5e0c94-2fd7-4ff9-9a29-b48d21ec0d62" />


## References
Grimm, V., Railsback, S. F., Vincenot, C. E., Berger, U., Gallagher, C., DeAngelis, D. L., Edmonds, B., Ge, J., Giske, J., Groeneveld, J., Johnston, A. S. A., Milles, A., Nabe-Nielsen, J., Polhill, J. G., Radchuk, V., Rohwäder, M.-S., Stillman, R. A., Thiele, J. C., & Ayllón, D. (2020). The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update to Improve Clarity, Replication, and Structural Realism. Journal of Artificial Societies and Social Simulation, 23(2), 7. https://doi.org/10.18564/jasss.4259

Leyk, S., Binder, C. R., & Nuckols, J. R. (2009). Spatial modeling of personalized exposure dynamics: The case of pesticide use in small-scale agricultural production landscapes of the developing world. International Journal of Health Geographics, 8, 17. https://doi.org/10.1186/1476-072X-8-17

Olszewska-Guizzo, A., Sia, A., Fogel, A., & Ho, R. (2022). Features of urban green spaces associated with positive emotions, mindfulness and relaxation. Scientific Reports, 12(1), 20695. https://doi.org/10.1038/s41598-022-24637-0

Yang, L. E., Hoffmann, P., Scheffran, J., Rühe, S., Fischereit, J., & Gasser, I. (2018). An Agent-Based Modeling Framework for Simulating Human Exposure to Environmental Stresses in Urban Areas. Urban Science, 2(2), 36. https://doi.org/10.3390/urbansci2020036
