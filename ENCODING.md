Here are the codes (i.e.) actions I intend to use into a discrete space in Gymnasium. For now, we ignore military units as they do not take part of the level (Hunting). The following actions are:

**Do nothing**

Ditto

**Create a villager**

Select TC (press hotkey(, then click on create villager button. This should be pressing a key, then clicking on a given position for the villager

**Gather Food** 

Select villager, idle or not and right click on food source. Food sources are animals and forage bushes for now (skip Farms for now)

A bit more complicated is if we want to fish as not all fish is accessible to villager (must be on shore)

**Gather Wood** 

Select villager, idle or not and right click on wood source. 

**Build house**

Select villager (first idle, then find one in the map), place house on free land (the complicated part here), build it.

Now, there are some map functions which complement the ones before:

**Shift in direction x for t miliseconds** 

Shifts in a x degrees angle for  t miliseconds. That is a parametrised move. This might prove too ambitious.

**Click on map**

There is a mini-map. Click on it.


**REPRESENTATION**

We will represent this gene as a probability vecto of length 7 (meaning probability to choose a certain solution). Hence, all elements should be between 0 and 1 and sum to 1.


  
