# bug-tracker-migration-test

Trial run for importing the nublado.org Trac tickets as GitHub issues.

  * This time I will stick to markdown (instead of org-mode) for the README, in case anyone else wants to edit it
  * The plan is to use the XML-RPC API of the Trac site to get all the data out of the bug tracker
  
  
## Tools to use ##

There are several projects that do all or some of this semi-automatically

  * tracboat - this is designed for migrating to gitlab, but the first part (getting the data from Trac) is the same, and it is perhaps more full-featured than the github-specific projects
  * migrate-trac-issues-to-github - There are lots of versions of this
      * The most developed one seems to be [behrisch/migrate-trac-issues-to-github](https://github.com/behrisch/migrate-trac-issues-to-github) (last updated Dec 2017)
      * But there are some others that may have useful tweaks see [network graph](https://github.com/behrisch/migrate-trac-issues-to-github/network)

## Summary of history ##

  
## Log of testing tracboat ##

  * This has lots of independent parts, which makes it easy to play with 
    * 2019-10-16 : clone the package from <https://github.com/tracboat/tracboat>
        * Install using `pipenv`
        * Could not get to run because of issue with XML-RPC authentication on the nublado.org site
    * 2019-10-19 : found workaround for the authentication issue
        * Managed to run it to dump the Trac database to a json file
            ```
            pipenv run tracboat export --format json --out-file ~/tmp/nublado-trac-export.json --trac-uri=https://www.nublado.org/xmlrpc --no-ssl-verify
            ```
            
## Log of testing migrate-trac-issues-to-github ##
