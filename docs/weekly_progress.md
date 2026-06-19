Week-1  Completed Work :
    1. Raspberry Pi Lite OS installation.
    2. Setting up the OS and Installing different tools required to build a connection between the Raspberry Pi and other Sensors such as python , pip3 , i2c , smbus2 and so on as required. 
    3. Creating a connection between Raspberry and VL53L0X sensor.
    4. Writing the code required to initialize the VL53L0X sensor and testing the sensor at different distance making sure it is working properly and saving the results in CSV format as well.
    5. Creating a connection between the TCA9548A and Raspberry Pi and then connecting different sensors to TCA9548A and operating all of them at once.
    6. Testing all the other VL53L0X sensors through the MUX(TCA9548A) making sure all are working fine or not.
    7. Starting the basic research work, collecting all the necessary research papers regarding the SystemC , RISC-V , UAV testing , Obstacle detection , Swarms formation and so on.
    8. Adding all the necessary details required from the research papers we found and categorizing them into 2 different sections, adding the details  into the Google sheet table properly formatted and made by Imtishal.
       
Challenges faced during week-1: 
    1. First before we begin with OS installation we need to burn the Raspberry Pi iso image into a SD-card. However the iso image was not getting burned properly and causing issue during installation process. Reason ?  for this was the SD-card was not properly formatted I.e the space was not properly allocated to any section of the card  causing errors during read and write process. Solution? The solution to this issue was that we properly format the SD-card, then burn the ISO images and  install the OS,and thus after doing each step carefully we were successful in installing the OS.
       
    2. Second Problem we faced was the connection of MUX with the sensor. The MUX(TCA9548A) was not properly detecting the sensor we connected with it even tho the code written was correct. Reason ? The SDA wire  of sensor was connected with the SC0 part of the mux and SCA wire was connected with SD0 which was wrong it should be connected in opposite way. SCA→SC0 and SDA→SD0. Solution? After identifying this issue we properly connected the sensors and everything started working fine as usual. Thus all VL53L0X sensors were detected and working fine, similarly all the output port of the MUX(TCA9548A) were working fine and giving correct output.

Plan for Monday : 

    1. Learn about how to integrate the camera with the raspberry pi.
