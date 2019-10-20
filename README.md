# bug-tracker-migration-test

Trial run for importing the nublado.org Trac tickets as GitHub issues.

  * This time I will stick to markdown (instead of org-mode) for the README, in case anyone else wants to edit it
  * Please do not open any [Issues](https://github.com/cloudy-astrophysics/bug-tracker-migration-test/issues) in this repo, since that is where we are going to try and dump the Trac tickets
  * The plan has two stages 
      1. To use the XML-RPC API of the Trac site to get all the data out of the ticket system
      2. To use the Github API to reconstruct the tickets as Github Issues
          * Map Components, Types, Priorities to Tags
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
        * This mostly works (it took about 30 min to go through everything), but there was a problem with retrieving the attachments
        * First tried to fix this by using python 2.7 interpreter in the pipenv, but that failed to compile some dependency, so I have abandoned that track
    * 2019-10-19 evening: 
        * Going back to python 3, I quickly found a fix to the attachment problem
        * To avoid having to grab the entire database by hand, I am testing functions by hand in a REPL.  For instance:
          ```python
          # Import tracboat/src/tracboat/trac.py
          import trac
          trac_uri="https://www.nublado.org/xmlrpc"
          source = trac.connect(
              trac_uri,
              encoding='UTF-8',
              use_datetime=True,
              ssl_verify=False
          )
          # Get a list of all the ticket IDs 
          ticket_ids = source.ticket.query("max=0&order=id")
          # Get the attachments from the latest ticket that has one
          att = trac.ticket_get_attachments(source, 430)
          # This returns a utf-8 bytes stream - decode it to string for printing
          print(att["ism.in"]["data"].decode())
          ```
          So that works for text attachments at least - I can't find any binary attachments to test on
    * Now that it is working, I am running it again on the entire database
        * Started at 20:42, Finished at 21:13 => 31 minutes run time
        * I neglected to decode the bytestream before writing to json, so it ended up getting converted into strange `bson` ascii encoding (something to do with MongoDB)
        * 
## Log of testing migrate-trac-issues-to-github ##
  * Following the documentation, I have set my GitHub credentials with `git config` 
      * I generated a token ([Settings/Developer settings/Personal access tokens](https://github.com/settings/tokens)), so I didn't have to use my actual password
      * Except it needed to be `github.user`, not `github.username`
  * Says it needs Python 2.7, but we will see if it is easy to fix for Python 3
  * It has one monolithic program `migrate.py`, but I am going to try and test the constituent parts
  
  
### Stage 1 – extract tickets from Trac ###
  
  * Slowly going through, fixing for python 3
  * Testing getting of tickets
    ```python
    m = Migrator(
        "https://www.nublado.org",
        github_username=github_username,
        github_password=github_password,
        github_project="cloudy-astrophysics/bug-tracker-migration-test",
        github_api_url="https://api.github.com",
        username_map={},
        config={"labels": {}}
    m.load_github()
    get_all_tickets = xmlrpclib.MultiCall(m.trac)
    )
    ```
    So far, so good, but then:
    ```python
    tickets = m.trac.ticket.query("max=0&order=id")
    ```
    fails with
    ```
    SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1056)
    ```
  * Luckily, I have `tracboat` to compare with. It turns out, we need to add the argument `context=ssl._create_unverified_context()` to `xmlrpclib.ServerProxy()`
  * Now that is fixed, I get a new error:
    ```
    ProtocolError: <ProtocolError for www.nublado.org//login/rpc: 401 Unauthorized>
    ```
  * Again, from `tracboat` they were using a different API url: <https://www.nublado.org/xmlrpc>, and when I switch to that it works
  * So I have got a few tickets:
    ```python
    get_all_tickets = xmlrpclib.MultiCall(m.trac)
    get_all_tickets.ticket.get(430)
    get_all_tickets.ticket.get(111)
    list(get_all_tickets())
    ```
    This works, but it doesn't get the attachments:
    ```
    [[430,
      <DateTime '20191008T12:10:38' at 0x10a3aba90>,
      <DateTime '20191008T12:10:38' at 0x10a3ab6d8>,
      {'status': 'new',
       'changetime': <DateTime '20191008T12:10:38' at 0x10a3abbe0>,
       '_ts': '1570536638433514',
       'description': 'The abundances command includes the keywords "no grains" and "no qheat" to modify the implicit grains that are included in certain mixtures.  The "no qheat" option does not work on c17 but works in c13 and the trunk.  A simple example is attached.  ',
       'reporter': 'gary',
       'cc': '',
       'resolution': '',
       'time': <DateTime '20191008T12:10:38' at 0x10a3ab908>,
       'component': 'grains',
       'summary': 'abundances ISM no qheat does not work on c17',
       'priority': 'blocker',
       'keywords': '',
       'version': 'c17_branch',
       'milestone': 'c17.02',
       'owner': 'peter',
       'type': 'defect - etc'}],
     [111,
      <DateTime '20091117T02:35:40' at 0x10a3abef0>,
      <DateTime '20190204T12:10:21' at 0x10a3ab668>,
      {'status': 'accepted',
       'changetime': <DateTime '20190204T12:10:21' at 0x10a3ab940>,
       '_ts': '1549282221449479',
       'description': 'The following model fails on trunk r3594 after failing to find an initial solution.  We appear to be at a temperature instability, and a very slightly less dense model (13.5575) finishes fine.  This model produces negative ion population errors in NI (and eventually all stages of nitrogen) but these are most likely unrelated to the root problems. \n{{{\nblackbody 1.16e7\nluminosity 37\nradius 10.48\nhden 13.5578\nstop zone 1\n}}}\n\n',
       'reporter': 'rporter',
       'cc': '',
       'resolution': '',
       'time': <DateTime '20091117T02:35:40' at 0x10a3ab0b8>,
       'component': 'thermal convergence',
       'summary': 'temperature instability',
       'priority': 'major',
       'keywords': '',
       'version': 'trunk',
       'milestone': 'c19 branch',
       'owner': 'peter',
       'type': 'defect - FPE'}]]
    ```
    * Comparing this output with the output from `tracboat`, we only have the `attributes` dict, and we are the missing the `attachments` dict and the `changelog` list of dicts.  The comments are part of `changelog`, but this also has edits to the description, title, etc
    * We could add this functionality by following the examples in tracboat's `ticket_get_changelog` and `ticket_get_attachments`.  Alternatively, we could use tracboat to dump the JSON file and then functions from `migrate.py` for the second step.  Either way, we should bear in mind the following: 
        1. We also would need to push the changelog and the attachments over the Github API, which might require a bit more research
        2. Tracboat uses a more straightforward method of making several separate xmlrpc api calls for each ticket, whereas `migrate.py` has a fancier method of queuing up all the queries with `xmlrpc.client.MultiCall()` and then just doing one network call for everything. This should be more efficient, but there are aspects of it that I still don't understand.
        3. We don't really need all of the changelog, but we *do* want the comments. Sometimes the comments have an empty `oldvalue`, which makes sense, but sometimes the `oldvalue` is a number, which I don't understand. **Aha, they do get the comments, see below**
    * Getting the comments with `Migrator.get_trac_comments()`
	  ```python
	  comments = m.get_trac_comments(111)
	  ```
	  yields
	  ```
      {'20091117T22:51:41': ['@rjrw changed description from:\n\n> The following model fails on trunk r3594 after failing to find an initial solution.  We appear to be at a temperature instability, and a very slightly less dense model (13.5575) finishes fine.  This model produces negative ion population errors in NI (and eventually all stages of nitrogen) but these are most likely unrelated to the root problems. \n> \n> blackbody 1.16e7\n> \n> luminosity 37\n> \n> radius 10.48\n> \n> hden 13.5578\n> \n> stop zone 1\n> \n> \n> \n\nto:\n\n> The following model fails on trunk r3594 after failing to find an initial solution.  We appear to be at a temperature instability, and a very slightly less dense model (13.5575) finishes fine.  This model produces negative ion population errors in NI (and eventually all stages of nitrogen) but these are most likely unrelated to the root problems. \n> \n> ```\n> blackbody 1.16e7\n> luminosity 37\n> radius 10.48\n> hden 13.5578\n> stop zone 1\n> ```\n> \n> \n\n'],
       '20091119T08:35:05': ['@rjrw changed attachment from "" to "conv_change"',
        '@rjrw commented:\n\n> Updated patch to deal with underflow problems on 64bit\n\n'],
       '20091120T12:15:03': ['@peter commented:\n\n> This is fixed on the mainline in r3610. This is the less invasive fix intended for c10_branch. Once we have branched, the more invasive patch intended for C12 that is attached to this PR will be applied to the trunk. So keeping this PR open until that has been done.\n\n',
        '@peter changed milestone from "" to "C12 branch"',
        '@peter changed owner from "nobody" to "peter"',
        '@peter changed status from "new" to "accepted"'],
       '20091120T12:19:49': ['@peter changed attachment from "" to "patch2"',
        '@peter commented:\n\n> updated patch wrt r3610\n\n'],
       '20190204T11:54:34': ['@peter changed milestone from "C13 branch" to "C19_branch"'],
       '20190204T12:10:21': ['@peter commented:\n\n> Milestone renamed\n\n',
        '@peter changed milestone from "C19_branch" to "c19 branch"']}
	  ```


### Stage 2 – create issues on github ###
  * This is handled by `Migrator.migrate_tickets()`
  * First half is preparing the data:
      1. Title is modified to include Trac ID
      2. Usernames are remapped (reporter and CC fields)
      3. Description is added to body (after transforming wiki syntax)
      4. All the attributes get appended to body as JSON
      5. Milestone and owner assigned
      6. Miscellaneous attributes get added as labels ('type', 'component', 'resolution', 'priority', 'keywords')
  * The second half finally engages with the github API
      1. Checks to see if title is already in the list of github issues, and if so edits it. *They recommend commenting this code out if running the script multiple times, and in fact we don't need this at all.* 
      2. Otherwise, makes a new issue on github using `Migrator.import_issue()`
  * Structure of `Migrator.import_issue()`
  
