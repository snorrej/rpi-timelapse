from datetime import datetime
import time
import os
import __future__

class Wrapper(object):

    def __init__(self, subprocess):
        self._subprocess = subprocess

    def call(self, cmd):
        p = self._subprocess.Popen(cmd, shell=True, stdout=self._subprocess.PIPE,
            stderr=self._subprocess.PIPE)
        out, err = p.communicate()
        return p.returncode, out.rstrip(), err.rstrip()

class SystemStats(Wrapper):
    """ A class which wraps system calls to measure temperature and voltage. """

    def __init__(self, subprocess):
        Wrapper.__init__(self, subprocess)
        self._CMD = 'vcgencmd'

    def stats(self):
        return self.voltage() + ' ' + self.temperature()

    def voltage(self):
        code, out, err = self.call(self._CMD + ' measure_temp')
        if code != 0:
            raise Exception(err)
        return out

    def temperature(self):
        code, out, err = self.call(self._CMD + ' measure_volts')
        if code != 0:
            raise Exception(err)
        return out

class Analyse(Wrapper):
    """ A class which wraps calls to the external jhead/imagemagick process. """

    def __init__(self, subprocess):
        Wrapper.__init__(self, subprocess)
        self._CMD = 'jhead'

    def mean_brightness(self, filepath):
	# Use the thumbnail for the mean brightness check, because it's faster than using the full image
        code, out, err = self.call(self._CMD + ' -st - ' + filepath + ' | identify -format "%[mean]" -')
        if code != 0:
            raise Exception(err)
        return out

class GPhoto(Wrapper):
    """ A class which wraps calls to the external gphoto2 process. """

    def __init__(self, subprocess):
        Wrapper.__init__(self, subprocess)
        self._CMD = '/usr/bin/gphoto2'
        self._shutter_choices = None
        self._aperture_choices = None
        self._iso_choices = None

    def get_camera_date_time(self):
        code, out, err = self.call(self._CMD + " --get-config /main/settings/datetime")
        timestr = None
        for line in out.split('\n'):
            if line.startswith('Current:'):
                timestr = line[line.find(':'):]
        if not timestr:
            raise Exception('No time parsed from ' + out)
        stime = time.strptime(timestr, ": %Y-%m-%d %H:%M:%S")
        return stime

    def capture_image_and_download(self):
        code, out, err = self.call(self._CMD + " --capture-image-and-download --filename '%Y%m%d%H%M%S.JPG'")
        filename = None
        for line in out.split('\n'):
            if line.startswith('Saving file as '):
                filename = line.split('Saving file as ')[1]
                os.unlink('webkamera-tmp.jpg')
                os.rename(filename,'webkamera-tmp.jpg')
                os.unlink('webkamera.jpg')
                os.symlink('webkamera-tmp.jpg','webkamera.jpg')
        return filename

    def get_shutter_speeds(self):
        code, out, err = self.call([self._CMD + " --get-config /main/capturesettings/shutterspeed"])
        choices = {}
        current = None
        for line in out.split('\n'):
            if line.startswith('Choice:'):
                choices[line.split(' ')[2]] = line.split(' ')[1]
            if line.startswith('Current:'):
                current = line.split(' ')[1]
        self._shutter_choices = choices
        return current, choices

    def set_shutter_speed(self, secs=None, index=None):
        code, out, err = None, None, None
        if secs:
            if self._shutter_choices == None:
                self.get_shutter_speeds()
            code, out, err = self.call([self._CMD + " --set-config /main/capturesettings/shutterspeed=" + str(secs)])
        if index:
            code, out, err = self.call([self._CMD + " --set-config /main/capturesettings/shutterspeed=" + str(index)])

    def get_aperture(self):
        code, out, err = self.call([self._CMD + " --get-config /main/capturesettings/shutterspeed"])
        choices = {}
        current = None
        for line in out.split('\n'):
            if line.startswith('Choice:'):
                choices[line.split(' ')[2]] = line.split(' ')[1]
            if line.startswith('Current:'):
                current = line.split(' ')[1]
        self._aperture_choices = choices
        return current, choices

    def set_aperture(self, ap=None, index=None):
        code, out, err = None, None, None
        if ap:
            if self._aperture_choices == None:
                self.get_aperture()
            code, out, err = self.call([self._CMD + " --set-config /main/capturesettings/aperture=" + str(ap)])
        if index:
            code, out, err = self.call([self._CMD + " --set-config /main/capturesettings/aperture=" + str(index)])

    def get_iso(self):
        code, out, err = self.call([self._CMD + " --get-config /main/imgsettings/iso"])
        choices = {}
        current = None
        for line in out.split('\n'):
            if line.startswith('Choice:'):
                choices[line.split(' ')[2]] = line.split(' ')[1]
            if line.startswith('Current:'):
                current = line.split(' ')[1]
        self._iso_choices = choices
        return current, choices

    def set_iso(self, iso=None, index=None):
        code, out, err = None, None, None
        if iso:
            if self._iso_choices == None:
                self.get_iso()
            code, out, err = self.call([self._CMD + " --set-config /main/imgsettings/iso=" + str(self._iso_choices[iso])])
        if index:
            code, out, err = self.call([self._CMD + " --set-config /main/imgsettings/iso=" + str(index)])

    def get_model(self):
	code, out, err = self.call([self._CMD + " --summary"])
        model = {} 
        for line in out.split('\n'):
            if line.startswith('Model:'):
                model = line.split(' ')
                model.pop(0)
        return ' '.join(model) 
