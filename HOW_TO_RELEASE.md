# Preparing a pyproj release

Preparing a pyproj release is a two-phase process.

## Phase 1: Release Candidate

In this phase, we want to ensure all the builds work on all platforms and methods
of distribution for the next release.

### Add the rc postfix

The first step in this phase is to update the version number `__version__` in `__init__.py`
to the next release `<major>.<minor>.<patch>`. Then, add the `rc` style
postfix following the[PEP-440](https://www.python.org/dev/peps/pep-0440/#pre-releases)
conventions starting with `rc0` (ex. `3.7.2rc0`). Make sure this is done on the `main` branch.

Commit the changes:

```bash
git add pyproj/__init__.py
git commit -m "MNT: Update version to 3.7.2rc0"
git push
```

### Review changes in the changelog

Review `docs/history.rst` and compare to list of merged pull requests since the previous release:

https://github.com/pyproj4/pyproj/pulls?q=sort%3Aupdated-desc+is%3Apr+is%3Amerged

If changes are needed make sure to commit and push them to the `main` branch.

### Create a tag on the repository

The next step is to create a tag with the same name as the version just added.
This can be done using the git command line or as part of creating a
GitHub Release (see next section).

If you'd like to do it from the command line then
make sure you are on the `main` branch first. For example:

```bash
git checkout main
git tag 3.7.2rc0
```

This creates a lightweight git tag.

Push the tag to github with:

```bash
git push --follow-tags
```

### Create a GitHub Release

1. Go to https://github.com/pyproj4/pyproj/releases.
2. Click "Draft a new release".
   a. Click "Select tag" and either:
   b. Select the release candidate tag you pushed from the command line.
3. Type the version tag you would like GitHub to create as part of this release (ex. `3.7.2rc0`).
4. Enter "X.Y.Zrc0" as the Release title using the version number you created.
5. Leave the description blank.
6. Check the box for "Set as a pre-release".
7. Check the box for "Create a discussion for this release".
8. Click "Publish release".

### Test the release builds

1. Check the wheels built under GitHub Actions
   [here](https://github.com/pyproj4/pyproj/actions/workflows/release.yaml).
2. Verify wheel and sdist upload to PyPI at
   https://pypi.org/project/pyproj/X.Y.Zrc0/#files modifying the X.Y.Z for your release.
3. Update the release discussion (see below section)
4. Create a draft PR at https://github.com/conda-forge/pyproj-feedstock and verify tests pass (see below section).
5. Verify Debian builds were successful on the release discussion.
6. Verify Fedora builds were successful on the release discussion.
7. Verify the docs build successfully.

### Update release discussion

The GitHub release process above created a discussion at
https://github.com/pyproj4/pyproj/discussions/. Find that discussion
and update the post with information about what builds to check:

```
Release Candidate 0 Status:

- [ ] Conda Forge
- [ ] Debian: https://buildd.debian.org/status/package.php?p=python-pyproj&suite=experimental
- [ ] Fedora

Thanks for any testing that you can do.
```

See previous release candidate discussions for debian and fedora package
maintainers to mention for help.

### Create a draft conda-forge PR

The instructions below assume you:

1. Have an existing local conda environment with the `conda-smithy` package
   installed and updated.
2. You have a personal fork of the
   https://github.com/conda-forge/pyproj-feedstock repository on GitHub.
3. You have a local updated clone of the conda-forge feedstock repository and
   a git remote for your fork.

To create a feedstock pull request to test the release candidate:

1. Create a new branch for the PR based on the main branch:

   ```bash
   git checkout main
   git checkout -b dep-372
   ```

2. In a browser, go to
   https://pypi.org/project/pyproj/3.7.2rc0/#pyproj-3.7.2rc0.tar.gz but
   for the version you're releasing and copy the SHA256.
3. Edit `recipe/meta.yaml` and update the version number and the SHA256.
   Make sure to reset the build number to 0 and update any dependencies
   if necessary.
4. Add and commit these updates:

   ```bash
   git add recipe/meta.yaml
   git commit -m "Update version to 3.7.2rc0"
   ```

5. Rerender the feedstock with conda-smithy:

   ```bash
   conda smithy regenerate -c auto
   ```

6. Push the changes to your fork's remote.

   ```bash
   git push -u <your_fork>
   ```

7. Go to https://github.com/conda-forge/pyproj-feedstock and create a **draft**
   pull draft request with your new branch.

8. Do **NOT** merge the pull request. It will be updated during the final release process.

## Phase 2: Make the release

After the candidate has proven itself, it will be promoted to a final release.

### Remove the rc postfix

Remove the `rc` postfix from the the version number `__version__` in `__init__.py` (ex. `3.7.2rc0` -> `3.7.2`).

### Create a tag on the repository

The next step is to create a tag with the name `<major>.<minor>.<patch>`. This can be done using the git command line or
as part of the GitHub release. For example:

```
git tag -a 3.7.2 -m "Version 3.7.2"
```

This creates an annotated git tag meant for releases.

Push the tag to github with:

```bash
git push --follow-tags
```

### Create a GitHub Release

1. Go to https://github.com/pyproj4/pyproj/releases.
2. Click "Draft a new release".
3. Click "Select tag" and either:
   a. Select the release candidate tag you pushed from the command line.
   b. Type the version tag you would like GitHub to create as part of this release (ex. `3.7.2`).
4. Enter "X.Y.Z Release" as the Release title using the version number you created.
5. Click "Generate release notes".
6. Check the box for "Set as the latest".
7. Click "Publish release".

For more information on auto-generated release notes see
[automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)). Make sure to acknowledge contributions made by others in the release.

### The wheels

The wheels are tested with each merge to main and uploaded to https://pypi.anaconda.org/scientific-python-nightly-wheels/simple in GitHub Actions. They are uploaded to pypi on pre-release and release in GitHub Actions.

### Verify conda-forge build is correct

A PR for `pyproj` will be generated automatically after you push to pypi.
Verify all is correct on the PR at https://github.com/conda-forge/pyproj-feedstock.

### Update the docs

On the `gh-pages` branch, update the stable symlink to point to the next version.

```bash
git checkout gh-pages
git pull
ln -sfTv 3.7.2 stable
git add stable
git commit -n -m "stable -> 3.7.2"
```

The `T` flag in the `ln` command ensures that "stable" is treated as a file,
and not as a directory to create the symbolic link inside of. The `-n` flag
on `git commit` is needed if you had previously installed `pre-commit` as the
`gh-pages` branch does not have a pre-commit config and pre-commit will fail.
The `-n` flag skips pre-commit checks.

## Preparing for the next release

To put the repository in a state for the next release cycle:

1. Edit `docs/history.rst`.
2. Add a new "Latest" section header to the top of the version list.
3. Edit `docs/past_versions.rst` and add the recent release. For example:

   ```
   - `3.7.0 <https://pyproj4.github.io/pyproj/3.7.0/>`_
   ```

4. Edit `__version__` in `pyproj/__init__.py` for the next release (ex. `3.7.0` -> `3.7.1.dev0`)
5. Commit and push these changes to `main`.
