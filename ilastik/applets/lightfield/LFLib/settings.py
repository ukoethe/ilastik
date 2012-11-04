import os

id = os.environ["LOGNAME"]


if id=="swanner":
    print "I'am on dodo!"    
    BASEPATHS = {
           "Buddha":"/home/swanner/data/lightfields/HCI_Buddha/",
           "Mona":"/home/swanner/data/lightfields/HCI_Mona/",
           "Cone":"/home/swanner/data/lightfields/HCI_ConeHead/",
           "Still":"/home/swanner/data/lightfields/StillLife/",
           "Bronze":"/home/swanner/data/lightfields/BronzeMan/"
           }
               
elif id == "lfa":
    print "I'am on lfa!"  
    BASEPATHS = {
               "Buddha":"/data/lfa/LightFields/blender/HCI_Buddha/",
               "Mona":"/data/lfa/LightFields/blender/HCI_Mona/",
               "Cone":"/data/lfa/LightFields/blender/HCI_ConeHead/",
               "Still":"/data/lfa/LightFields/blender/StillLife/",
               "Bronze":"/data/lfa/LightFields/BronzeMan/"
               }
    
elif id == "sven":
    BASEPATHS = {
               "Buddha":"/home/sven/data/lightfields/HCI_Buddha/",
               "Mona":"/home/sven/data/lightfields/HCI_Buddha/",
               "Cone":"/home/sven/data/lightfields/HCI_Buddha/",
               "Still":"/home/sven/data/lightfields/StillLife/"
               }
    
  
lfs = {
 "buddha":{
           "clean":{
                 "5x5":BASEPATHS["Buddha"]+"buddha_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Buddha"]+"buddha_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Buddha"]+"buddha_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Buddha"]+"buddha_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Buddha"]+"buddha_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Buddha"]+"buddha_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Buddha"]+"buddha_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Buddha"]+"buddha_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Buddha"]+"buddha_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Buddha"]+"buddha_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Buddha"]+"buddha_bl02_1024_9x9_rgb.h5"
                },
            "noisy":{
                 "5x5":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Buddha"]+"buddhaCamnoise_bl02_1024_9x9_rgb.h5"
              },
           "cycles":{
                     "9x9":BASEPATHS["Buddha"]+"buddhaCycles_9x9_rgb.h5"
              }
           },
  "mona":{
          "clean":{
                 "5x5":BASEPATHS["Mona"]+"mona_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Mona"]+"mona_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Mona"]+"mona_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Mona"]+"mona_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Mona"]+"mona_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Mona"]+"mona_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Mona"]+"mona_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Mona"]+"mona_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Mona"]+"mona_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Mona"]+"mona_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Mona"]+"mona_bl02_1024_9x9_rgb.h5"
              },
            "noisy":{
                 "5x5":BASEPATHS["Mona"]+"monaCamnoise_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Mona"]+"monaCamnoise_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Mona"]+"monaCamnoise_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Mona"]+"monaCamnoise_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Mona"]+"monaCamnoise_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Mona"]+"monaCamnoise_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Mona"]+"monaCamnoise_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Mona"]+"monaCamnoise_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Mona"]+"monaCamnoise_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Mona"]+"monaCamnoise_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Mona"]+"monaCamnoise_bl02_1024_9x9_rgb.h5"
              }
           },
  "cone":{
          "clean":{
                 "5x5":BASEPATHS["Cone"]+"conehead_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Cone"]+"conehead_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Cone"]+"conehead_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Cone"]+"conehead_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Cone"]+"conehead_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Cone"]+"conehead_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Cone"]+"conehead_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Cone"]+"conehead_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Cone"]+"conehead_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Cone"]+"conehead_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Cone"]+"conehead_bl02_1024_9x9_rgb.h5"
              },
            "noisy":{
                 "5x5":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_5x5_rgb.h5",
                 "7x7":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_7x7_rgb.h5",
                 "9x9":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_9x9_rgb.h5",
                 "11x11":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_11x11_rgb.h5",
                 "13x13":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_13x13_rgb.h5",
                 "15x15":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_15x15_rgb.h5",
                 "17x17":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_17x17_rgb.h5",
                 "256":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_256_9x9_rgb.h5",
                 "512":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_512_9x9_rgb.h5",
                 "896":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_896_9x9_rgb.h5",
                 "1024":BASEPATHS["Cone"]+"coneheadCamnoise_bl02_1024_9x9_rgb.h5"
              }
           },
   "still":{
          "clean":{
                 "9x9":BASEPATHS["Still"]+"stillLife_bl02_9x9_rgb.h5",
                 "17x17":BASEPATHS["Still"]+"stillLife_bl02_17x17_rgb.h5"
              }
           },
    "bronze":{
          "clean":{
                 "9x9":BASEPATHS["Bronze"]+"bronzeMan_9x9_rgb.h5"
              }
           }
 
 }
 
