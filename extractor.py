import sys, os, shutil, io, subprocess
import libs.mpk, libs.lay, libs.mvl_steam_CHN
from contextlib import redirect_stdout



class Extractor():
    def __init__(self, profile):
        self.skipextract = False
        self._profile = profile
        self.__process = None
        self.dl = ""
        self.out = io.StringIO()
        match self._profile.filetype:
            case "mpk":
                self._extractor = self.extract_mpk
            case "cpk": 
                self._extractor = self.extract_cpk
            case "psb.m":
                self._extractor = self.extract_psbm
            case "": #maybe should change to copy, so plain convert operations work
                self._extractor = lambda x,y,z: print(f"Skipping extraction: {y}")
            case _: #attempt to copy individual files to a sprite folder
                pass
        match self._profile.processor:
            case "lay":
                self._processor = self.lay_process
            case "chn-mvl":
                self._processor = self.chn_mvl_process
        if sys.platform != 'win32': #create a variable to store a wineserver process object later and check if it's already running
            self.wserv = None
        if "--force-wine" in sys.argv or shutil.which('mono') == None:

            self.forcewine = True
        else:
            print("By default mono is used for compatible programs, if you encounter issues, use --force-wine to use wine instead", file=sys.stderr)
            self.forcewine = False
        self.stopped = False
        self.done = False
        self.status = "Ready"
        self.convert = False
        self.delconv = True

    def extract_mpk(self, path, arch, dest):
        linkcopy(os.path.join(path, arch), os.path.join(dest, arch))
        print("Extracting " + arch)
        libs.mpk.main(os.path.join(dest, arch))
        print("Removing temporary " + arch)
        os.remove(os.path.join(dest, arch))

    def extract_cpk(self, path, arch, dest):
        exeargs = [os.path.abspath('CriPakTools.exe'), os.path.join(path, arch), "ALL"]
        print("Extracting " + arch)
        cwd = os.path.join(dest, arch.removesuffix(".cpk"))
        os.mkdir(cwd)
        self.runexe(exeargs, cwd)


    def extract_psbm(self, path, arch, dest):
        keydet = self._profile.mkey.split(" ")
        if keydet[0] == "detect":
            self._profile.mkey = findgamekey(os.path.join(path, keydet[1]))
            print("Found game key: ",self._profile.mkey)
        del keydet
        base = arch.removesuffix("_info.psb.m")
        linkcopy(os.path.join(path, arch), os.path.join(dest, arch), False)
        linkcopy(os.path.join(path, base + "_body.bin"), os.path.join(dest, base + "_body.bin"), False)
        if arch in self._profile.sprites and self.convert:
            print("Encountered sprite file, will be extracted twice")
            exeargs = [os.path.abspath('freemote/PsbDecompile.exe'), 'info-psb', os.path.join(dest, arch), '-k', self._profile.mkey]
            self.runexe(exeargs, dest)
            shutil.move(os.path.join(dest, base), os.path.join(dest, base + "-psb"))
        exeargs = [os.path.abspath('freemote/PsbDecompile.exe'), 'info-psb', os.path.join(dest, arch), '-k', self._profile.mkey, '-a']
        print("Extracting and decompiling " + arch)
        #p = subprocess.Popen(exeargs, stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = cwd, text=True, universal_newlines=True)
        self.runexe(exeargs, dest)
        print(f"Removing temporary {arch} and {arch.removesuffix("info.psb.m") + "body.bin"}")
        os.remove(os.path.join(dest, arch))
        os.remove(os.path.join(dest, arch.removesuffix("info.psb.m") + "body.bin"))

    def lay_process(self, file):
        basefile = os.path.basename(file)
        print(f"Processing: {basefile}")
        libs.lay.main(file, piece=False)
        if self.delconv:
            os.remove(file)
            os.remove(file.removesuffix("_.lay") + ".png")
            print(f"Deleted {basefile}, {basefile.removesuffix('_.lay')}.png")

    def chn_mvl_process(self, file):
        basefile = os.path.basename(file)
        print(f"Processing: {basefile}")
        if int(basefile) % 2 == 0:
            self.__pic = basefile
        else:
            os.chdir(os.path.dirname(file))
            libs.mvl_steam_CHN.main(basefile, self.__pic)
            if self.delconv:
                os.remove(self.__pic)
                os.remove(basefile)
                print(f"Deleted {basefile}, {self.__pic}")
            del self.__pic
            os.chdir(os.path.dirname(sys.argv[0]))

    def extract(self, path, archives, dest):
        self.stopped = False
        self.total = len(archives)
        self.progress = 0
        for self.progress, arch in enumerate(archives):
            with redirect_stdout(self.out):
                if self.stopped:
                    self.status = "Canceled"
                    print("\nCancelled because of user input")
                    break
                self.status = "Extracting: " + arch
                if self.skipextract:
                    continue
                self._extractor(path, arch, dest)
        if self.stopped:
            return
        if self.convert:
            self.process(dest, archives) #switch to a list of archives or folders
        with open("main.log", "w") as file:
            file.write(self.out.getvalue())
        self.progress += 1
        if self.stopped:
            return
        self.status = "Done"
        self.stopped = True
        self.done = True

    def process(self, path, archives):
        selected = [x for x in self._profile.sprites if x in archives]
        with redirect_stdout(self.out):
            for spr in selected :
                fsdir = os.path.join(path, spr.removesuffix("." + self._profile.filetype))
                files = os.listdir(fsdir)
                files = [f for f in files if f.endswith(self._profile.pfiletype)]
                print(f"Starting processing from {spr}")
                self.total = len(files)
                self.progress = 0
                for self.progress, file in enumerate(files):
                    if self.stopped:
                        self.status = "Canceled"
                        print("\nCancelled because of user input")
                        return
                    self.status = f"Processing: {file} from {spr}"
                    self._processor(os.path.join(fsdir, file))

    def stop(self):
        self.stopped = True
        sys.stderr.writeline('stopped')
        if self.__process != None:
            self.__process.terminate()
            self.__process.kill()


    def download(self):
        from urllib import request
        with open(self.dlfile, "wb") as f:
            with request.urlopen(url=self.dl) as req:
                f.write(req.read())

    def runexe(self, exeargs, cwd, wine=False):
        env = dict()
        if sys.platform != 'win32':
            if wine or self.forcewine:
                prefdir = os.path.abspath('wineprefix')
                env['WINEPREFIX'] = prefdir
                exeargs = [shutil.which('wine')] + exeargs
                if self.wserv == None:
                    print("Starting wineserver, if this is the first time this might take a while. If asked to, install mono")
                    os.makedirs(prefdir, exist_ok=True)
                    self.wserv = subprocess.Popen([shutil.which('wineserver'), "-p5"], env=env) #speed up multiple file processing by keeping wine running for 5 seconds after a process has exited
                    while self.wserv.poll() == None:
                        pass #wait for the process to exit and daemon to start
            else:
                exeargs = [shutil.which('mono')] + exeargs
        self.__process = subprocess.Popen(exeargs, stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = cwd, text=True, universal_newlines=True, env=env)
        while self.__process.poll() == None:
            self.out.write(self.__process.stdout.readline())
            #sys.stderr.write(self.__process.stderr.readline()) # Blocking operation, too lazy to figure out not blocking
            if self.stopped:
                        if self.__process.poll() == None:
            print("process running outside of capture loop, THIS SHOULD NEVER HAPPEN", file=sys.stderr)
        self.__process.wait()
        self.out.writelines(self.__process.stdout.readlines())
        sys.stderr.writelines(self.__process.stderr.readlines()) # attempt to passthrough stderr to stderr

def findgamekey(file):
    with open(file, "rb") as game:
        barray = game.read()
        script = barray.find(b"script_body.bin")
        if script == -1:
            return ""
        game.seek(script - 16)
        return game.read(16).rstrip(b"\00").decode()

def linkcopy(src, dest, symlink=True):
    if symlink:
        try: #So does windows support symlinks or not?
            os.symlink(src, dest)
            print("Creating a link for " + os.path.basename(src))
            return
        except OSError:
            pass
    try: # If in the unlikely scenario the symlink fails, let's hard link
        os.link(src, dest)
        print("Creating a link for " + os.path.basename(src))
        return
    except OSError: # Now how the hell did we get here? Easily, just disable symlinks and run across multiple drives
        print("Copying " + os.path.basename(src))
        shutil.copy(src, dest)
        return

