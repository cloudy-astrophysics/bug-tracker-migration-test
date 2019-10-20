# bug-tracker-migration-test

Trial run for importing the nublado.org Trac tickets as GitHub issues.

  * This time I will stick to markdown (instead of org-mode) for the README, in case anyone else wants to edit it
  * Please do not open any [Issues](https://github.com/cloudy-astrophysics/bug-tracker-migration-test/issues) in this repo, since that is where we are going to try and dump the Trac tickets
  * The plan has two stages 
      1. To use the XML-RPC API of the Trac site to get all the data out of the ticket system
      2. To use the Github API to reconstruct the tickets as Github Issues
          * Map Types to Tags
          * Map Milestones to Milestones
          * Map Trac users to github users (anyone without a github username becomes a tag)
          * Carry over attachments 
  
  
## Tools to use ##

There are several projects that do all or some of this semi-automatically

  * tracboat – this is designed for migrating to gitlab, but the first part (getting the data from Trac) is the same, and it is perhaps more full-featured than the github-specific projects
  * migrate-trac-issues-to-github – There are lots of versions of this
      * The most developed one seems to be [behrisch/migrate-trac-issues-to-github](https://github.com/behrisch/migrate-trac-issues-to-github) (last updated Dec 2017)
      * But there are some others that may have useful tweaks see [network graph](https://github.com/behrisch/migrate-trac-issues-to-github/network)

## Summary of history ##

  
## Log of testing tracboat ##

  * This has lots of independent parts, which makes it easy to play with 
    * 2019-10-16 : clone the package from <https://github.com/tracboat/tracboat>
        * Install using `pipenv`
        * Could not get to run because of issue with XML-RPC authentication on the nublado.org site
    * 2019-10-19 morning: found workaround for the authentication issue
        * Managed to run it to dump the Trac database to a json file
          ```
          pipenv run tracboat export --format json --out-file ~/tmp/nublado-trac-export.json --trac-uri=https://www.nublado.org/xmlrpc --no-ssl-verify
          ```
        * This mostly works (it took about 20 min to go through everything), but there was a problem with retrieving the attachments
        * First tried to fix this by using python 2.7 interpreter in the pipenv, but that failed to compile some dependency, so I have abandoned that track
    * 2019-10-19 evening: 
        * Going back to python 3, I quickly found a fix to the attachment problem
        * To avoid having to grab the entire database by hand, I am testing functions by hand in a REPL.  For instance:
          ```python
          import trac
          trac_uri="https://www.nublado.org/xmlrpc"
          source = trac.connect(
              trac_uri,
              encoding='UTF-8',
              use_datetime=True,
              ssl_verify=False
          )
          ticket_ids = source.ticket.query("max=0&order=id")
          att = trac.ticket_get_attachments(source, 430)
          print(att["ism.in"]["data"].decode())
          ```

## Log of testing migrate-trac-issues-to-github ##
