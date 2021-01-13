# Printing Methods
The naming convention will be that of the original parts. The bottom portion is the largest portion, with the flat portions for the thrusters. The top portion is the dome that fits on top of the bottom portion. The cap is the bottommost part of the robot. This part has all the holes and screws in to prevent the ballast from falling out.

There are two main methods to print the robot, FDM or SLS. Whether you are printing in SLS or FDM, it is very important to check the tolerances of the specific printer you are using. FDM requires a lot of post processing. This can take a few days. SLS, on the other hand does not require much post processing. It is also the most waterproof method and most accurate, and therefore the most expensive. It is always best to test changes in FDM before printing in SLS. 


# Waterproofing Motors
To waterproof the brushless DC motors, first remove the e-clamp with pliers and separate the motor into its respective halves. Clean the wire coil array using isopropyl alcohol and protect the bearings with some wax of your choice. Cover the bearings with a few layers of painters tape for protection. Now add a few layers of painters tape around the part to make a makeshift crucible to hold the epoxy as it flows into the wire coils. For the next steps, use marine grade epoxy. The epoxy was mixed with slow hardener and poured into the coils. After waiting a day for the epoxy to cure, take off the tape and remove the excess epoxy (a lathe works best but is not required). Make sure the motor can spin once all the excess epoxy is removed. 


# Post Processing (if using FDM)
If the robot has been printed in FDM, there will be a number of things to post process. Step one is to remove all the support material from wherever it is visible. There will be support material inside the screw holes for the thrusters that should be drilled out. The drainage holes on the side of the robot must also be drilled out as those will also be filled with support material. Another point to consider is the support material inside the o-ring groove. Be careful not to take off any actual material as this will cause the o-ring to fail and the robot will fill with water. The last place to look, other than the obvious places, is the inside of the cap piece, where it interfaces with the bottom portion. This usually fills with support material and might have to be taken out. The next step is to make sure all the propellers fit on the motors. Sand the inside of the propellers as needed. 

The last thing to do when post processing FDM is to epoxy places in the robot where water will enter through the material. When looking at the robot, there will be places where the material seems to have small holes. These need to be filled with epoxy. Furthermore, you will have to epoxy the hexagonal hole as well as its subsequent circular hole on the outside and inside. Check the entire robot for small cracks and holes and epoxy as needed. Keep the epoxy handy as it will be used to put parts of the robot together.

This step is for after you put the MT30 connectors in. Let the epoxy dry and dunk the bottom portion in water up till the base of the o-ring support. Make sure the inside does not fill up with water. If it does, epoxy as needed. Do this with the top portion as well, making sure everything is water sealed. 


# Putting the Robot Together
Whether the robot is printed in SLS or FDM, there will be a building process for the robot. All of the electrical work to be done is outlined in the electrical documentation. This only focuses on the mechanical aspects of assembly. Step one is the heated inserts. To set these inserts, the team used a flat tip soldering iron. Set the insert on top of where it is supposed to go. Touch the tip of the iron to the insert and within a few seconds it should start sinking into place. Where to place the inserts: Directly to the right and left of the MT30 connector holes (triangular holes on the bottom portion), the three small holes in the cap, in the bottom portion where it will interface with the top portion. There will be three spots for the heated inserts on the hexagonal extrusion for the electrical stack. All of these locations are shown below. 

The next step is epoxying the MT30 connecters in the bottom portion. Put the epoxy on the sides of the connector and insert it into the bottom portion. Test the waterproofness as mentioned in the last paragraph of post processing. 

Now you must assemble the thrusters. Insert the motor into the propeller and screw down the assembly to its respective propeller housings. Insert the metal dowels in the 4 corners of the housings. Epoxy those in if necessary (although it probably is tight enough once fitted on the bottom portion). Once those are prepared, it is best to finish the electrical stack and figure out how much ballast is required. 

After all of that is done, the next step is to put in the ballast weight (possible weight inside the vehicle) and the electrical stack. Now connect the electrical stack to its respective places on the MT30 connector and connect the motor housings to their respective places on the bottom portion. Connect the thrusters to their spots on the MT30 connectors and screw the housing into the bottom portion. At this point, you should be done with the bottom portion. The next step is to insert the o-rings and put the top portion on the robot. Lastly, put the ballast trim weights on the bottom and close the cap. Screw in at least one of the holes on the cap so it does not rotate in water. 

<img src="../Images/AboveHull.jpg?raw=true" alt="Bottom Portion" width="275"/>
<img src="../Images/ThrusterConnection.jpg?raw=true" alt="Vertical Thruster Connection" width="275"/>
<img src="../Images/BottomComponent.jpg?raw=true" alt="Bottom Locking Component" width="275"/>

 
# O-Rings
To create a water seal between the top portion and the bottom portion, the team used a double o-ring design. The following resources were used to make the groove for the o-ring. The team used a 162 size soft o-ring. This o-ring has been calculated to stretch anywhere from 1-2% and compress from 20-21%. This takes into account the tolerances of SLS printers and FDM printers such as a MakerBot. [This website][1] will give out the design considerations for the gland design.

After calculating the height of the groove, it is important to consider the width of the top and bottom of the groove. The bottom of the groove should be no smaller than the cross sectional diameter of the o-ring. The width of the top should be decided by calculating the cross sectional area of the o-ring and making sure it is wide enough to accommodate the entire o-ring. It is best to choose a width that makes the cross sectional area of the groove as close as possible to the actual cross sectional area of the o-ring, making sure that the cross sectional area of the groove is not smaller than that of the o-ring.  

<img src="../Images/ORingDiagram.jpg?raw=true" alt="O-Ring Diagram" width="400"/>

Above is the groove design for a 162 soft o-ring. The height of the groove is 1.7mm, allowing for a 20-21% compression ratio and a 1-2% stretch. The angle was chosen to make sure that the entirety of the compressed o-ring will fit in the groove. The bottom is 2.62mm which is the cross sectional diameter of the o-ring.



# Components of Design
There are certain components in this robot’s design where its purpose may not be immediately clear. This section is meant to mitigate that confusion and familiarize the user with the robot’s features.
1.	Ballast: The robot has a place to put brass weights to balance out the robot. Each of these holes (shown by the blue arrow) have a spot for 1 inch brass weights. This was designed so one could place a brass weight with accuracy up to ½ the diameter of the weight. All the holes inside the ballast holes make sure the ballast area fills up with water (shown by the orange arrow). These holes are connected to the holes that outline the outside of the robot. The three small holes (designated by the yellow arrow) is where the cap would be screwed into the bottom portion to keep the cap from rotating underwater. 

<img src="../Images/BottomPortionFromBottom.png?raw=true" alt="View from the bottom of the bottom portion" width="400"/>

2.	Wireless charging and hexagonal insert: Looking at the bottom portion from the top shows a hexagonal hole leading into a circular hole (orange arrow). The hexagonal hole is meant to interface with the hexagonal extrusion from the electrical stack (see section on puttin the robot together for more information). This keeps the electrical stack stationary during use. The circular part is meant to fit a wireless charger in it so the robot does not have to be taken apart to charge. 

<img src="../Images/BottomPortionFromTop.jpg?raw=true" alt="View from the top of the bottom portion" width="300"/>

[1]: https://www.marcorubber.com/o-ring-groove-design-considerations.htm

