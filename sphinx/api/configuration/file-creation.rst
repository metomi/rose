.. _User: http://man.openbsd.org/ssh_config#User

.. _File Creation Mode:

File Creation Mode
==================

The application launcher will use the following logic to determine the
root directory to install file targets with a relative path:

#. If the setting :rose:conf:`rose-app.conf|file-install-root=PATH` is
   specified in the application configuration file, its value will be used.
#. If the environment variable :envvar:`ROSE_FILE_INSTALL_ROOT` is
   specified, its value will be used.
#. Otherwise, the working directory of the task will be used.

.. rose:file:: *

   .. rose:conf:: schemes

      :opt fs: The file system scheme. If a URI looks like an existing path
         in the file system, this scheme will be used.
      :opt namelist: The namelist scheme. Refer to ``namelist:NAME``
         sections in the configuration file.
      :opt svn: The Subversion scheme. The location is a Subversion URL or
         an FCM location keyword. A URI with these schemes ``svn``,
         ``svn+ssh`` and ``fcm`` are automatically recognised.
      :opt git: The Git scheme. The location is complex due to Git semantics.
         It must have the scheme ``git`` and be of the form
         ``git:REPOSITORY_URL::PATHSPEC::TREEISH``:
         
         * ``REPOSITORY_URL`` should
           be a Git repository URI which may itself have a scheme ``ssh``,
           ``git``, ``https``, or be of the form ``HOST:PATH``, or ``PATH`` for
           local repositories.
         * ``PATHSPEC`` should be a path to a file or
           directory that you want to extract.
           The ``PATHSPEC`` must end with a
           trailing slash (``/``) if it is a directory. To extract from the root
           of the repository use a ``PATHSPEC`` of ``./`` e.g.
           ``git:git@github.com:metomi/rose::./::2.2.0``.
         * ``TREEISH`` should be a tag,
           branch, or long commit hash to specify the commit at which you want
           to extract.

         These should follow the same semantics as if you git
         cloned ``REPOSITORY_URL``, git checkout'ed ``TREEISH``, and extracted
         the path ``PATHSPEC`` within the clone. It may help to think
         of the parts of the location as ``git:Where::What::When``.
         
         ..rubric:: Examples:

         .. code-block:: rose

           # Download the sphinx directory from the master branch of
           # the github.com/metomi/rose repo. Note trailing slash.
           [file:rose-docs]
           source=git:git@github.com:metomi/rose::sphinx/::master

           # Extract the whole contents of version 2.0.1 of the local
           # repository at /home/user/some/path/to/my/git/repo.
           [file:all_of_my_repo]
           source=git:/home/user/some/path/to/my/git/repo::./::2.0.1

           # Extract a single file from a particular commit of a repo
           # on a machine that we have ssh access to.
           [file:my_file]
           source=git:machine01:/data/user/my_repo_name::etc/my_file::7261bff4d9a6c582ec759ef52c46dd794fe8794e

         You should set ``git config uploadpack.allowFilter true`` and
         optionally ``git config uploadpack.allowAnySHA1InWant true`` on
         repositories if you are setting them up to pull from.
      :opt rsync: This scheme is useful for pulling a file or directory from
         a remote host using ``rsync`` via ``ssh``. A URI should have the
         form ``HOST:PATH``.

      Rose will automatically attempt to detect the type of a source
      (i.e. file, directory, URL), however, the name of the source can
      sometimes be ambiguous. E.g. A URL with a ``http`` scheme can be a
      path in a version control system, or a path to a plain file. The
      :rose:conf:`schemes` setting can be used to help the system to do
      the right thing. The syntax is as follows:
      
      .. code-block:: rose

         schemes=PATTERN-1=SCHEME-1
                =PATTERN-2=SCHEME-2

      For example:

      .. code-block:: rose

         schemes=hpc*:*=rsync
                =http://host/svn-repos/*=svn

         [file:foo.txt]
         source=hpc1:/path/to/foo.txt

         [file:bar.txt]
         source=http://host/svn-repos/path/to/bar.txt

      In the above example, a URI matching the pattern ``hpc*:*`` would use the
      ``rsync`` scheme to pull the source to the current host, and a URI
      matching the pattern ``http://host/svn-repos/*`` would use the
      ``svn`` scheme. For all other URIs, the system will try to make an
      intelligent guess.

      .. note::

         The system will always match a URI in the order as specified by the
         setting to avoid ambiguity.

      .. note::

         If the ``rsync`` scheme is used you can use the `User`_ setting in
         ``~/.ssh/config`` to specify the user ID for logging into ``HOST``
         if required.


   .. rose:conf:: file:TARGET

      .. rose:conf:: source=SOURCE & source=(SOURCE)

         A space delimited list of sources for generating this file. A
         source can be the path to a regular file or directory in the
         file system (globbing is also supported - e.g. using ``"\*.conf"``
         to mean all ``.conf`` files), or it may be a URI to a resource. If
         a source is a URI, it may point to a section with a supported
         scheme in the current configuration, e.g. a
         ``namelist:NAME`` section. Otherwise the URI must be in a
         supported scheme or be given sufficient information for the system to
         determine its scheme, e.g. via the :rose:conf:`*|schemes` setting.

         .. tip::
            Normally, a source that does not exist would trigger an error in run
            time. However, it may be useful to have an optional source for a file
            sometimes. In which case, the syntax :rose:conf:`source=(SOURCE)`
            can be used to specify an optional source. E.g.
            ``source=namelist:foo (namelist:bar)`` would allow
            ``namelist:bar`` to be missing or ignored without an error.
 
         .. note::

            File creation can be triggered with use of the metadata triggers. An
            example can be found :ref:`here <trigger-file-creation>`. 
      
      .. rose:conf:: checksum

         The expected MD5 checksum of the target. If specified, the file
         generation will fail if the actual checksum of the target does not
         match with this setting. This setting is only meaningful if
         ``TARGET`` is a regular file or a symbolic link to a regular file.

         .. note::

            An empty value for checksum tells the system to report the target
            checksum in verbose mode.

      .. rose:conf:: mode

         :default: auto

         :opt auto: Automatically determine action based on the value of
            :rose:conf:`source`.

            * :rose:conf:`source=` - If source is undefined create an empty
              file.
            * :rose:conf:`source=path` - If source is a single path to a file
              or directory then the path will be copied to the target path.
            * :rose:conf:`source=file1 file2 ...` - If the source is a list of
              files then the files will be concatenated in the target path.
            * :rose:conf:`source=dir1 dir2 ...` - If the source is a list of
              directories then the directories will be transferred to the target
              path using ``rsync``.

         :opt mkdir: Creates an empty directory (:rose:conf:`source` must be a
             single path).
         :opt symlink: Creates a symlink to the provided source, the
             source *does not* have to exist when the symlink is created (
             :rose:conf:`source` must be a single path).
         :opt symlink+: Creates a symlink to the provided source, the source
             *must* exist when the symlink is created (:rose:conf:`source`
             must be a single path).
