Web Client Commands
====================

Using tox:
----------

* Run the test suite::
    
    tox -egrunt test


* Run a local development server::

    tox -egrunt serve


* Run a local development server without the API::

    tox -egrunt_no_api serve


* Package the distro::

    tox -egrunt build


Using grunt directly within virtual environment
-----------------------------------------------

* Activate virtual environment::
    
    source .tox/grunt/bin/activate


* Update/refresh the javascript build and runtime dependencies::

    npm prune
    npm install
    bower prune
    bower install


* Run a local development server with API and web client::

    grunt serve


* Run the test suite::

    grunt test


* Package the distro::

    grunt build


* Bootstrap your database::

  ./bin/api.sh create-db


* Migrate the database::

    ./bin/api.sh migrate-db


* Start the API::

    ./bin/api.sh start

* Stop the API::

    ./bin/api.sh stop
