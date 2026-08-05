The confidence level tells how much the UAV is confident about the object it receives Range [0 , 1] and if the distance between the UAV and the osbtacle is very low then confidence level is very high.

The Perception then first gets the confidence value of the  UAV and applies different scenario errors like false negative,false positive and sensor dropout and so on.

Now after inducing the error how to fix it,  by using Fusion method if fusion is enabled then it gathers all the data of the UAV obtacles detection some might miss and some might not(Perception error cannot effect every UAV on board) then it avg the obstacle detection confidence 	and overwrites it with the each UAVs self obstacle based detection confidence. This way we can recover the obstacle missed by the UAV.


The repulsive term
For every detection the UAV currently perceives (obstacle or other UAV), it builds a vector pointing away from that thing, then makes it stronger the closer the threat is:
strength = avoidance_gain / r
where r is the distance to the threat. Halve the distance, double the push. This is a very standard robotics technique called an artificial potential field — obstacles act like they're "repelling" the UAV, the goal acts like it's "attracting" it, and the final motion is just the sum of all these forces.



Phantams are nothing but the false positive in the world which randomly gets injected into the world causing the UAVs uncessarily steer away from the path causing an increase of power consumption and also the code increses the count of uncessarily avoidance count in the code. This error is usually caused by the sensor rather than the environment itself.
