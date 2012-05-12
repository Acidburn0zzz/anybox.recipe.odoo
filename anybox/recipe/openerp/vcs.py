import os
import subprocess
import logging
from utils import working_directory_keeper

logger = logging.getLogger(__name__)

SUBPROCESS_ENV = os.environ.copy()
SUBPROCESS_ENV['PYTHONPATH'] = SUBPROCESS_ENV.pop(
    'BUILDOUT_ORIGINAL_PYTHONPATH', '')

SUPPORTED = frozenset(('bzr', 'hg', 'git', 'svn'))

def hg_get_update(target_dir, url, revision, offline=False):
    """Ensure that target_dir is a clone of url at specified revision.

    If target_dir already exists, does a simple pull.
    Offline-mode: no clone nor pull, but update.
    """
    if not os.path.exists(target_dir):
        # TODO case of local url ?
        if offline:
            raise IOError("hg repository %r does not exist; cannot clone it from %r (offline mode)" % (target_dir, url))

        logger.info("CLoning %s ...", url)
        clone_cmd = ['hg', 'clone']
        if revision:
            clone_cmd.extend(['-r', revision])
        clone_cmd.extend([url, target_dir])
        subprocess.call(clone_cmd, env=SUBPROCESS_ENV)
    else:
        # TODO what if remote repo is actually local fs ?
        if not offline:
            logger.info("Pull for hg repo %r ...", target_dir)
            subprocess.call(['hg', '--cwd', target_dir, 'pull'],
                            env=SUBPROCESS_ENV)
        if revision:
            logger.info("Updating %s to revision %s",
                        target_dir, revision)
            up_cmd = ['hg', '--cwd', target_dir, 'up']
            if revision:
                up_cmd.extend(['-r', revision])
            subprocess.call(up_cmd, env=SUBPROCESS_ENV)

def bzr_get_update(target_dir, url, revision, offline=False):
    """Ensure that target_dir is a branch of url at specified revision.

    If target_dir already exists, does a simple pull.
    Offline-mode: no branch nor pull, but update.
    """
    import pdb; pdb.set_trace()
    rev_str = revision and '-r ' + revision or ''

    with working_directory_keeper:
        if not os.path.exists(target_dir):
            # TODO case of local url ?
            if offline:
                raise IOError("bzr branch %s does not exist; cannot branch it from %s (offline mode)" % (target_dir, url))

            os.chdir(os.path.split(target_dir)[0])
            logger.info("Branching %s ...", url)
            subprocess.call('bzr branch --stacked %s %s %s' % (
                    rev_str, url, target_dir), shell=True)
        else:
            os.chdir(target_dir)
            # TODO what if bzr source is actually local fs ?
            if not offline:
                logger.info("Pull for branch %s ...", target_dir)
                subprocess.call('bzr pull', shell=True)
            if revision:
                logger.info("Update to revision %s", revision)
                subprocess.call('bzr up %s' % rev_str, shell=True)

def git_get_update(target_dir, url, revision, offline=False):
    """Ensure that target_dir is a branch of url at specified revision.

    If target_dir already exists, does a simple pull.
    Offline-mode: no branch nor pull, but update.
    """
    rev_str = revision

    with working_directory_keeper:
        if not os.path.exists(target_dir):
            # TODO case of local url ?
            if offline:
                raise IOError("git repository %s does not exist; cannot clone it from %s (offline mode)" % (target_dir, url))

            os.chdir(os.path.split(target_dir)[0])
            logger.info("CLoning %s ...", url)
            subprocess.call('git clone -b %s %s %s' % (
                    rev_str, url, target_dir), shell=True)
        else:
            os.chdir(target_dir)
            # TODO what if remote repo is actually local fs ?
            if not offline:
                logger.info("Pull for git repo %s (rev %s)...",
                            target_dir, rev_str)
                subprocess.call('git pull %s %s' % (url, rev_str),
                                shell=True)
            elif revision:
                logger.info("Checkout %s to revision %s",
                            target_dir,revision)
                subprocess.call('git checkout %s' % rev_str, shell=True)

def svn_get_update(self, target_dir, url, revision, offline=False):
    """Ensure that target_dir is a branch of url at specified revision.

    If target_dir already exists, does a simple pull.
    Offline-mode: no branch nor pull, but update.
    """
    rev_str = revision and '-r ' + revision or ''

    with working_directory_keeper:
        if not os.path.exists(target_dir):
            # TODO case of local url ?
            if offline:
                raise IOError("svn checkout %s does not exist; cannot checkout  from %s (offline mode)" % (target_dir, url))

            os.chdir(os.path.split(target_dir)[0])
            logger.info("Checkouting %s ...", url)
            subprocess.call('svn checkout %s %s %s' % (
                    rev_str, url, target_dir), shell=True)
        else:
            os.chdir(target_dir)
            # TODO what if remote repo is actually local fs ?
            if offline:
                logger.warning(
                    "Offline mode: keeping checkout %s in its current rev",
                    target_dir)
            else:
                logger.info("Updating %s to location %s, revision %s...",
                            target_dir, url, revision)
                # switch is necessary in order to move in tags
                # TODO support also change of svn root url
                subprocess.call('svn switch %s' % url, shell=True)
                subprocess.call('svn up %s' % rev_str,
                                shell=True)


