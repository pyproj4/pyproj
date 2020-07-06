# Preparing a pyproj release

Preparing a pyproj release is a two-phase process.

## Phase 1: Release Candidate

In this phase, we want to ensure all the builds work on all platforms and methods
of distribution for the next release.

### Add the rc postfix

The first step in this phase is to update the version number `__version__` in `__init__.py`
to the next release `<major>.<minor>.<patch>`. Then, add the `rc` style posfix following the [PEP-440](https://www.python.org/dev/peps/pep-0440/#pre-releases) conventions.

### Create a tag on the repository

The next step is to create a tag with the same name as the version just added. This can be done using the git command line or from https://github.com/pyproj4/pyproj/tags.

### Test the release builds

1. Create a draft PR at https://github.com/pyproj4/pyproj-wheels and verify tests pass.
2. Create a draft PR at https://github.com/conda-forge/pyproj-feedstock and verify tests pass.
3. Verify Windows wheels built properly.
4. Verify Debian builds were succesful.
5. Verify the docs build successfully.

## Phase 2: Make the release

After the candidate has proven itself, it will be promoted to a final release.

### Remove the rc postfix

Remove the `rc` postfix from the the version number `__version__` in `__init__.py`.

### Create a tag on the repository

The next step is to create a tag with the name `<major>.<minor>.<patch>`. This can be done using the git command line or from https://github.com/pyproj4/pyproj/tags.

Next, go through the history and add release notes. Make sure to acknowledge contributions made by others in the release. A useful script for automating this task for code contributions is the [pandas announce script](https://github.com/pandas-dev/pandas/blob/bb6135880e5e453d7701764b9f2e4ad3356a68d7/doc/sphinxext/announce.py).

### The wheels

1. Update the PR at https://github.com/pyproj4/pyproj-wheels with the release tag, merge, and download wheels.
2. Retrieve Windows wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs.

### Create the release sdist

1. Make sure the directory is clean and checkout the release tag.
2. `python setup.py sdist`

### Upload to pypi

Upload the wheels and the sdist `tar.gz` for the release to pypi.

### Verify conda-forge build is correct

A PR for `pyproj` will be generated automatically after you push to pypi.
Verify all is correct on the PR at https://github.com/conda-forge/pyproj-feedstock.

### Update the docs

On the `gh-pages` branch, update the stable symlink to point to the next version.
