import os
import time
import tempfile
import shutil
import asyncproc
import signal
import string

__all__ = ['call_with_timeout']

def with_timeout(code, stdout_cb, stderr_cb, timeout, files):
    """Call some python code with a callback executed on each line
    
    Parameters
    ----------
    scriptcode : string
        python code to execute
    stdout_cb : function
        A callback executed on each line, as it arrives
    stderr_cb : function
        A callback executed on the the error, all at the end
    timeout : int
        How long do you want to execute the code for?
        
    Returns
    -------
    timed_out : bool
    """

    # do a little validation
    if not isinstance(files, list):
        print 'files is bad type'
        return
    for f in files:
        if ('name' not in f) or ('contents' not in f):
            print 'wrong keys in f', f
            return
        if os.path.split(f['name'])[0] != '':
            print 'path is too long. should be in this directory', f
            return
        if os.path.splitext(f['name'])[1] not in ['.pdb', '.prmtop', '.inpcrd']:
            print 'extension is wrong', f
            return

    
    tempdir = tempfile.mkdtemp()
    invocation = time.time()
    initial_working_directory = os.curdir
    os.chdir(tempdir)
    codefile = os.path.join(tempdir, 'openmm.py')
    try:
        with open('openmm.py', 'w') as f:
            f.write(str(code))
        for f in files:
            print 'saving f', f['name']
            with open(f['name'], 'w') as fh:
                fh.write(f['contents'])
        
        # run python in unbuffered mode
        cmd = [which('python'), '-u', codefile]
        p = asyncproc.Process(cmd)
        
        invocation_time = time.time()
        finished = False
        while (time.time() - invocation_time < timeout) and not finished:
            out, err = p.readboth()

            # if we saw any stdout/stderr report it
            if len(err) > 0:
                stderr_cb(err)
            if len(out) > 0:
                stdout_cb(out)

            if p.finished():
                return False  # saying we DIDN'T time out

            sleep_time = 0.1 # seconds
            time.sleep(sleep_time)


        # print 'killing...'
        p.kill(signal.SIGKILL)
        p.wait()
        # print '...kill done'
        return True

    finally:
        shutil.rmtree(tempdir) 
        os.chdir(initial_working_directory)

def which(filename):
   """Find an executable in $PATH, like the which command in bash
   """
   search_path = os.environ['PATH']
   file_found = 0
   paths = string.split(search_path, os.pathsep)
   for path in paths:
      if os.path.exists(os.path.join(path, filename)):
          file_found = 1
          break
   if file_found:
      return os.path.abspath(os.path.join(path, filename))
   else:
      return None
