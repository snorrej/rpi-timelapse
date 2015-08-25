#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import time
import sys
import os

from wrappers import GPhoto
from wrappers import Analyse
from wrappers import SystemStats

logfile = os.path.dirname(os.path.realpath(__file__)) + "/timelapse.log"
sys.stdout = open(logfile, 'w')

MIN_INTER_SHOT_DELAY_SECONDS = timedelta(seconds=30)
TARGET_BRIGHTNESS = 32000 # Acceptable values +/- 20% , 32000 seems to be a good value if 3/4 of image is sky 

#Canon EOS 400D / EF-S 18-55mm f/3.5-5.6 II
CONFIGS = [
("1/1000", 100, "22"),
("1/1000", 100, "20"),
("1/1000", 100, "18"),
("1/1000", 100, "16"),
("1/1000", 100, "14"),
("1/1000", 100, "13"),
("1/1000", 100, "11"),
("1/1000", 100, "10"),
("1/1000", 100, "9"),
("1/1000", 100, "8"),
("1/1000", 100, "7.1"),
("1/1000", 100, "6.3"),
("1/1000", 100, "5.6"),
("1/1000", 100, "4.5"),
("1/1000", 100, "4"),
("1/1000", 100, "3.5"),
("1/800", 100, "3.5"),
("1/640", 100, "3.5"),
("1/500", 100, "3.5"),
("1/400", 100, "3.5"),
("1/320", 100, "3.5"),
("1/250", 100, "3.5"),
("1/200", 100, "3.5"),
("1/160", 100, "3.5"),
("1/125", 100, "3.5"),
("1/100", 100, "3.5"),
("1/80", 100, "3.5"),
("1/60", 100, "3.5"),
("1/50", 100, "3.5"),
("1/40", 100, "3.5"),
("1/30", 100, "3.5"),
("1/25", 100, "3.5"),
("1/20", 100, "3.5"),
("1/15", 100, "3.5"),
("1/13", 100, "3.5"),
("1/10", 100, "3.5"),
("1/8", 100, "3.5"),
("1/6", 100, "3.5"),
("1/5", 100, "3.5"),
("1/4", 100, "3.5"),
("0.3", 100, "3.5"),
("0.4", 100, "3.5"),
("0.5", 100, "3.5"),
("0.6", 100, "3.5"),
("0.8", 100, "3.5"),
("1", 100, "3.5"),
("1.3", 100, "3.5"),
("1.6", 100, "3.5"),
("2.5", 100, "3.5"),
("3.2", 100, "3.5"),
("4", 100, "3.5"),
("5", 100, "3.5"),
("3.2", 200, "3.5"),
("4", 200, "3.5"),
("5", 200, "3.5"),
("6", 200, "3.5"),
("8", 200, "3.5"),
("10", 200, "3.5"),
("6", 400, "3.5"),
("8", 400, "3.5"),
("10", 400, "3.5"),
("13", 400, "3.5"),
("15", 400, "3.5"),
("10", 800, "3.5"),
("13", 800, "3.5"),
("15", 800, "3.5"),
("20", 800, "3.5"),
("25", 800, "3.5"),
("30", 800, "3.5"),
("20", 1600, "3.5"),
("25", 1600, "3.5"),
("30", 1600, "3.5")
]

def main():
    print "Timelapse starting at %s" % (time.asctime())
    camera = GPhoto(subprocess)
    info = Analyse(subprocess)
    sysinfo = SystemStats(subprocess)

    current_config = 19
    shot = 0
    failures = 0
    prev_acquired = None
    last_acquired = None
    last_started = None

    try:
        while True:
            last_started = datetime.now()
            shot = shot + 1
            config = CONFIGS[current_config]
            print "Shot %d : %s" % (shot, time.asctime())
            print "Shot %d : Shutter: %ss , ISO: %d , Ap: %s" % (shot, config[0], config[1], config[2])
            sys.stdout.flush()

            camera.set_shutter_speed(secs=config[0])
            camera.set_iso(iso=str(config[1]))
            camera.set_aperture(ap=config[2])
            try:
              filename = camera.capture_image_and_download()
            except Exception, e:
              print "Error on capture: " + str(e)
              failures += 1
              if failures > 2:
                  print "3 successive failures: the camera doesn't work!"
                  sys.stdout.flush()
                  break
              print "Retrying..."
              sys.stdout.flush()
              # Occasionally, capture can fail but retries will be successful.
              continue
            failures = 0
            #print "Shot %d Filename: %s" % (shot, filename)
            sys.stdout.flush()

            prev_acquired = last_acquired
            brightness = float(info.mean_brightness('webkamera-tmp.jpg'))
            last_acquired = datetime.now()

            #health = sysinfo.stats()

            print "Shot %d : Brightness: %s " % (shot, brightness)
            sys.stdout.flush()

            if brightness < TARGET_BRIGHTNESS * 0.9 and current_config < len(CONFIGS) - 1:
                if TARGET_BRIGHTNESS - brightness > TARGET_BRIGHTNESS * 0.44 and current_config < len(CONFIGS) - 2:
                    current_config += 2
                    print "Shot %d : EV step: +2/3" % (shot)
                else:
                    current_config += 1
                    print "Shot %d : EV step: +1/3" % (shot)
            elif brightness > TARGET_BRIGHTNESS * 1.1 and current_config > 0:
                if brightness - TARGET_BRIGHTNESS > TARGET_BRIGHTNESS * 0.44 and current_config > 2:
                    current_config -= 2
                    print "Shot %d : EV step: -2/3" % (shot)
                else:
                    current_config -= 1
                    print "Shot %d : EV step: -1/3" % (shot)
            else:
                if last_started and last_acquired and last_acquired - last_started < MIN_INTER_SHOT_DELAY_SECONDS:
                    sleep_for = max((MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started)).seconds, 0);
                    print "Sleeping for %ss ..." % str(sleep_for)
                    sys.stdout.flush()
                    time.sleep(sleep_for)
    except Exception,e:
        print str(e)


if __name__ == "__main__":
    main()
