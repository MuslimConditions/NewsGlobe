import os
import ftplib
import time

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


def get_all_files_in_directory(directory="", relative=True, unix_style=True):
    out = []
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)
    for (path, dirs, files) in os.walk(dir_path):
        for file in files:
            if relative:
                path_n = os.path.join(path, file)[len(dir_path):]
            else:
                path_n = os.path.join(path, file)
            if unix_style:
                path_n = path_n.replace("\\", "/")
            out.append(path_n)
    return out


def get_all_subdirectories(directory="", relative=True, unix_style=True):
    out = []
    dirs = [x[0] for x in os.walk(os.path.join(os.path.dirname(os.path.realpath(__file__)), directory))]
    if relative:
        dirs = [x[0][len(os.path.join(os.path.dirname(os.path.realpath(__file__)), directory)):] for x in
                os.walk(os.path.join(os.path.dirname(os.path.realpath(__file__)), directory))]
    if unix_style:
        for d in dirs:
            out.append(d.replace('\\', '/'))
        dirs = out
    dirs.remove("")
    return dirs


def get_filename_from_filepath(path):
    if "\\" in path:
        return path.split("\\")[-1]
    return path.split("/")[-1]


def get_directory_from_filepath(path, unix_style=True):
    if unix_style:
        delimiter = '/'
    else:
        delimiter = '\\'
    if "\\" in path:
        return delimiter.join(path.split('\\')[:-1])
    if unix_style:
        return delimiter.join(path.split('/')[:-1])


# noinspection PyIncorrectDocstring
def traverse(ftp, depth=0):
    """
    return a recursive listing of an ftp web_app contents (starting
    from the current directory)

    listing is returned as a recursive dictionary, where each key
    contains a contents of the subdirectory or None if it corresponds
    to a file.

    @param ftp: ftplib.FTP object
    :param depth:
    """
    if depth > 10:
        return ['depth > 10']
    level = {}
    for entry in (path for path in ftp.nlst() if path not in ('.', '..')):
        try:
            ftp.cwd(entry)
            level[entry] = traverse(ftp, depth + 1)
            ftp.cwd('..')
        except ftplib.error_perm:
            pass
        except:
            raise
    return level


def recursive_print_dict(dictionary, prev="/", storage=None, delimiter="/"):
    """ Recursively prints nested dictionaries."""
    if storage is None:
        storage = []
    for key, value in dictionary.items():
        storage.append(prev + key)
        if isinstance(value, dict):
            next_prev = prev + key + delimiter
            recursive_print_dict(value, next_prev, storage)
    return storage


def get_ftp_directory_list(ftp):
    d = traverse(ftp)
    out = recursive_print_dict(d)
    ftp.cwd("/")
    return out


def create_remote_subdirectories(ftp, local_dir="", remote_dir="/"):
    print("Creating remote subdirectories from local directory", local_dir, "to remote directory", remote_dir)
    if remote_dir[0] != "/":
        raise Exception("Remote directory has to be absolute, e.g: '/public_html'")
    local_dirs = get_all_subdirectories(local_dir)
    ftp.cwd(remote_dir)

    for d in local_dirs:
        splitted = d.split("/")
        splitted.remove("")
        ftp.cwd(remote_dir)

        for s in splitted:
            while True:
                try:
                    ftp.cwd(s)
                    break
                except ftplib.error_perm:
                    pwd = ftp.pwd()
                    print("Directory", s, "does not exist in", pwd)
                    cmd = pwd + "/" + s
                    try:
                        print("Creating", cmd)
                        ftp.mkd(cmd)
                    except ftplib.error_perm:
                        pass
    ftp.cwd("/")


# noinspection PyBroadException
def delete_all_files(ftp, remote_path=None):
    if remote_path:
        ftp.cwd(remote_path)
    for n in ftp.nlst():
        try:
            if n not in ('.', '..'):
                while True:
                    print("FTP: Processing", n)
                    try:
                        ftp.delete(n)
                        print('FTP: Deleted', n)
                        break
                    except ftplib.error_perm:
                        print("FTP:", n, 'not deleted, probably a directory, moving to', n)
                        try:
                            ftp.cwd(n)
                            delete_all_files(ftp)
                            ftp.cwd('..')
                            print('FTP: Trying to remove directory', n)
                            ftp.rmd(n)
                            print('FTP: Directory', n, 'removed!')
                            break
                        except:
                            pass
        except Exception:
            print('Trying to remove directory', n)
            ftp.rmd(n)
            print('FTP: Directory', n, 'removed!')


def upload_all_files(ftp, path, remote_path=None):
    files = os.listdir(path)
    os.chdir(path)
    if remote_path:
        ftp.cwd(remote_path)
    for f in files:
        print("FTP: Processing", f)
        if os.path.isfile(f):
            fh = open(f, 'rb')
            print("FTP: Uploading", f)
            ftp.storbinary('STOR %s' % f, fh)
            fh.close()
        elif os.path.isdir(f):
            try:
                ftp.mkd(f)
            except ftplib.error_perm as e:
                if "File exists" in str(e):
                    pass
            if ".disable_ftp_upload" not in os.listdir(f):
                ftp.cwd(f)
                upload_all_files(ftp, f)
            else:
                print("Ignoring folder:", f)
    ftp.cwd('..')
    os.chdir('..')


def update_all_files(ftp_host, ftp_port, ftp_username, ftp_password, ftp_rootdir):
    static_path = os.path.join(FILE_PATH, "static")
    while True:
        try:
            print("FTP: New FTP Session to newsglobe.dx.am...")
            ftp = ftplib.FTP()
            ftp.connect(ftp_host, ftp_port)
            ftp.login(ftp_username, ftp_password)
            upload_all_files(ftp, static_path, ftp_rootdir)
            ftp.quit()
            break
        except Exception as e:
            print("Exception:", str(e))
            print("Trying again in 5s...")
            time.sleep(5)
            pass
