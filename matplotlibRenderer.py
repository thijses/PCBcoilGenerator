"""
just a little test of matplotlib. I might do something with this later on, not sure yet.

TODO:
 - add line width (vertical and horizontal are different)
 - use scatter() instead of plot(), but keep the lines (and don't display dots)

 - find use (idk, maybe i could get into flux/field modeling???)

"""


import numpy as np
import matplotlib.pyplot as plt

def plot4d(coil: 'coilClass'): # stolen from the World Wide Web (whatever that is)
    renderedCoils: list[list[tuple[float,float]]] = [coil.renderAsCoordinateList(False), coil.renderAsCoordinateList(True)]
    renderedCoils[1].reverse() # reverse the second list to make it all 1 continuous & repeating line
    layerspacing = coil.calcLayerSpacing()
    list4D = np.zeros((len(renderedCoils[0])*coil.layers, 4))
    for layer in range(coil.layers):
        renderedCoil = renderedCoils[layer % 2]
        for i in range(len(renderedCoil)):
            list4D[i + len(renderedCoil)*layer] = [renderedCoil[i][0],renderedCoil[i][1],layer*layerspacing,(layer+1)/coil.layers]
    x = list4D[:, 0];  y = list4D[:, 1];  z = list4D[:, 2];  c = list4D[:, 3] # this format is plottable with a 3D scatter plot

    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(projection="3d")
    for layer in range(coil.layers): # draw 1 layer at-a-time (this forloop is really just a colormap, but stupid)
        indices = [len(renderedCoil)*layer, len(renderedCoil)*(layer+1)]
        if(layer > 0):   ax.plot(x[indices[0]-1:indices[0]+1], y[indices[0]-1:indices[0]+1], z[indices[0]-1:indices[0]+1], color='black') # draw the via as a line
        ax.plot(x[indices[0]:indices[1]], y[indices[0]:indices[1]], z[indices[0]:indices[1]]) # i couldn't get the scatter plot function to display lines, but this works for now
    plt.tight_layout()
    plt.show()

if __name__ == "__main__": # an example of how this file may be used
    from PCBcoilV2 import coilClass, shapes, ozCopperToMM
    coil = coilClass(turns=3, diam=20, clearance=1, traceWidth=1, layers=4, PCBthickness=0.8, copperThickness=ozCopperToMM(1), shape=shapes['circle'], formula='cur_sheet') # debug
    plot4d(coil)