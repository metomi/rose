# Rose: How to Contribute

## Report Bugs

Report bugs and request enhancement by opening an issue on
[Rose issues @ Github](https://github.com/metomi/rose/issues). If reporting a
bug, add a recipe for repeating it. If requesting an enhancement,
describe the use case in detail.

## New Contributors

Please read the [CLA](#contributor-licence-agreement-and-certificate-of-origin).

Please add your name to the
[Code Contributors](#code-contributors) section of this file as part of your
first Pull Request (for each Cylc repository you contribute to).

## Contribute Code

We use [semver](https://semver.org/) to separate riskier changes (e.g. new features
& code refactors) from bugfixes to provide more stable releases for production environments.

**Enhancements** are made on the `master` branch and released in the next minor version
(e.g. 2.1, 2.2, 2.3).

**Bugfixes** and minor usability enhancements are made on bugfix branches and
released as the next maintenance version (e.g. 2.0.1, 2.0.2, 2.0.3). E.G. if the issue is on a `2.0` milestone, branch off of `2.0.x` to
develop your bugfix, then raise the pull request against the `2.0.x` branch. We will later merge the `2.0.x` branch into `master`.

We use [towncrier](https://towncrier.readthedocs.io/en/stable/index.html) for
generating the changelog. Changelog entries are added by running
```
towncrier create <PR-number>.<break|feat|fix>.md --content "Short description"
```

## Code Contributors

The following people have contributed to this code under the terms of
the Contributor Licence Agreement and Certificate of Origin detailed
below:

<!-- start-shortlog -->
 - Sadie Bartholomew (Met Office, UK)
 - Andrew Clark (Met Office, UK)
 - Kerry Day (Met Office, UK)
 - Martin Dix (CSIRO, Australia)
 - Ben Fitzpatrick (Met Office, UK)
 - Craig MacLachlan (Met Office, UK)
 - Joseph Mancell (Met Office, UK)
 - Dave Matthews (Met Office, UK)
 - Hilary Oliver (National Institute of Water and Atmospheric Research, New Zealand)
 - Annette Osprey (NCAS Computational Modelling Services, UK)
 - Stephen Oxley (Met Office, UK)
 - Matt Pryor (Met Office, UK)
 - Oliver Sanders (Met Office, UK)
 - Jon Seddon (Met Office, UK)
 - Harry Shepherd (Met Office, UK)
 - Matt Shin (Met Office, UK)
 - Tomasz Trzeciak (Met Office, UK)
 - Stuart Whitehouse (Met Office, UK)
 - Steve Wardle (Met Office, UK)
 - Scott Wales (ARC Centre of Excellence for Climate Systems Science, Australia)
 - Thomas Coleman (Bureau of Meteorology, Australia)
 - Declan Valters (Met Office, UK)
 - Paul Cresswell (Met Office, UK)
 - Bruno P. Kinoshita (National Institute of Water and Atmospheric Research, New Zealand)
 - Tim Pillinger (Met Office, UK)
 - Mel Hall (Met Office, UK)
 - Ronnie Dutta (Met Office, UK)
 - Roddy Sharp (Met Office, UK)
 - Mark Dawson (Met Office, UK)
 - Joe Marsh Rossney (UK Centre for Ecology & Hydrology)
 - Dimitrios Theodorakis (Met Office, UK)
 - Joseph Abram (Met Office, UK)
 - James Frost (Met Office, UK)
 - David Rundle (Met Office, UK)
 - Christopher Bennett (Met Office, UK)
<!-- end-shortlog -->

(All contributors are identifiable with email addresses in the version control
logs or otherwise.)

## Contributor Licence Agreement and Certificate of Origin

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I have
    the right to submit it, either on my behalf or on behalf of my
    employer, under the terms and conditions as described by this file;
    or

(b) The contribution is based upon previous work that, to the best of
    my knowledge, is covered under an appropriate licence and I have
    the right or permission from the copyright owner under that licence
    to submit that work with modifications, whether created in whole or
    in part by me, under the terms and conditions as described by
    this file; or

(c) The contribution was provided directly to me by some other person
    who certified (a) or (b) and I have not modified it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including my
    name and email address) is retained for the full term of
    the copyright and may be redistributed consistent with this project
    or the licence(s) involved.

(e) I, or my employer, grant to the UK Met Office and all recipients of
    this software a perpetual, worldwide, non-exclusive, no-charge,
    royalty-free, irrevocable copyright licence to reproduce, modify,
    prepare derivative works of, publicly display, publicly perform,
    sub-licence, and distribute this contribution and such modifications
    and derivative works consistent with this project or the licence(s)
    involved or other appropriate open source licence(s) specified by
    the project and approved by the
    [Open Source Initiative (OSI)](http://www.opensource.org/).

(f) If I become aware of anything that would make any of the above
    inaccurate, in any way, I will let the UK Met Office know as soon as
    I become aware.

(The Rose Contributor Licence Agreement and Certificate of Origin is
inspired by the Certificate of Origin used by Enyo and the Linux
Kernel.)
