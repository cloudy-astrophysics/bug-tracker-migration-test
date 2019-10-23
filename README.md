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
  * migrate-trac-issues-to-github (use MTITG for short) – There are lots of versions of this
      * The most developed one seems to be [behrisch/migrate-trac-issues-to-github](https://github.com/behrisch/migrate-trac-issues-to-github) (last updated Dec 2017)
      * But there are some others that may have useful tweaks see [network graph](https://github.com/behrisch/migrate-trac-issues-to-github/network)

## Summary of history ##
  * **2019-10-16:** Initial experiments with tracboat
  * **2019-10-19:** Got tracboat to work for dumping all issues to JSON, including attachments. This is a proof of concept that stage 1 can be done. But tracboat is no help with stage 2
  * **2019-10-19:** Start looking at MTITG - port to Python 3
  * **2019-10-20:** Initial test run of MTITG to import the first 10 issues from Trac. This works, except for the attachments.
  * **2019-10-21 morning:** Make a dedicated github account @cloudy-bot to do the migration work, so that my name is not written over everything
  * **2019-10-21 morning:** Discover that creating new milestones is not working (first 10 issues had no milestones). Fix that
  * **2019-10-21 morning:** Another test run, but from the @cloudy-bot account, importing up to issue #100 from Trac. This now includes some that are still open. Improved treatment of trac users without github accounts. 
  * **2019-10-21 evening:** Fix most of the problems with tags
  * **Remaining tasks:** Bring over attachments.
  
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
    ```js
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
      ```js
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

### Stage 1a Mapping of usernames ###
  * This is specified in a YAML config file, like this:
    ```yaml
    users:
      'gary / robin': CloudyLex
      gary: CloudyLex
      rjrw: rjrw
      will: will-henney
      mchatzikos: mchatzikos
      fguzman: fguzmanful
      # nicholas: MISSING
      # wangye0206: MISSING
      # dquan: MISSING
      # matt: MISSING
      # peter: MISSING
      # 'Peter, van, Hoof, <p.vanhoof@oma.be>': MISSING
      # rporter: MISSING
      # Ryan: MISSING
      # 'rporter@pa.uky.edu' MISSING
      # nobody: MISSING
      # somebody: MISSING
      # anonymous: MISSING
    ```
  * Most of the missing users can probably be ignored, but it might be worthwhile contacting the following:
      * Nick Abel
  * It looks like all the assignees will get notifications about their Issues when they are imported to GitHub, so I have made a separate config file `map-all-to-will.yaml` that maps all the Trac users to me (will-henney). I will use this during the testing stages, and then swap in the real mapping for the final migration. 
      * *Update*: Now that I have checked more carefully, it seems that there are no notifications, which is good
      * It is using the "new" issue import API, described at <https://gist.github.com/jonmagic/5282384165e0f86ef105>
      * On the other hand, although each issue and comment is annotated with the name of who wrote it, they all appear to have been created with the account that did the migration (currently me)
      * So, maybe it would be better to make a separate github account called `cloudy-migration-bot` or similar. 

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
  * 2019-10-20 – Add functionality to `migrate.py`
      * Specify a ticket range, so we don't do all 431 of them
      * Option for dry run, so we do everything *except* actually talk to GitHub
  * Help message for my new version
    ```
    $ ../migrate-trac-issues-to-github/migrate.py --help
    usage: migrate.py [-h] [--trac-username TRAC_USERNAME] [--trac-url TRAC_URL]
                      [--github-username GITHUB_USERNAME]
                      [--github-api-url GITHUB_API_URL]
                      [--github-project GITHUB_PROJECT]
                      [--username-map USERNAME_MAP]
                      [--trac-hub-config TRAC_HUB_CONFIG] [--ssl-verify]
                      [--dry-run] [--ticket-range TICKET_RANGE TICKET_RANGE]
     
    optional arguments:
      -h, --help            show this help message and exit
      --trac-username TRAC_USERNAME
                            Trac username (default: will)
      --trac-url TRAC_URL   Trac base URL (`USERNAME` and `PASSWORD` will be
                            expanded)
      --github-username GITHUB_USERNAME
                            Github username (default: will-henney)
      --github-api-url GITHUB_API_URL
                            Github API URL (default: https://api.github.com)
      --github-project GITHUB_PROJECT
                            Github Project: e.g. username/project
      --username-map USERNAME_MAP
                            File containing tab-separated Trac:Github username
                            mappings
      --trac-hub-config TRAC_HUB_CONFIG
                            YAML configuration file in trac-hub style
      --ssl-verify          Do SSL properly
      --dry-run             Do not actually import any issues into GitHub
      --ticket-range TICKET_RANGE TICKET_RANGE
                            First and last ticket IDs to process
    ```
	The last three options are ones that I have added. 
  * Trying it out
    ```
    ../migrate-trac-issues-to-github/migrate.py --trac-url=https://www.nublado.org --dry-run --ticket-range 1 10
    ```
  * That seemed to work, so I ran it without the `--dry-run`. This has put the first 10 tickets into the repo. Most of them were opened by Ryan. Note that we still do not have the attachments. That is what I will try and fix next. 

### Stage 2b - dealing with milestones ###
  * The first 10 issues did not have any milestones, but the next 10 do
  * This causes an error:
	```
    Adding milestone {'due': 0, 'completed': 0, 'description': 'This is the default milestone. It is appropriate for mainly for enhancements that are not time critical.', 'name': 'no milestone'}
    Exception: 'int' object has no attribute 'timetuple'
    > /Users/will/Dropbox/cloudy-github-migration/migrate-trac-issues-to-github/migrate.py(170)get_gh_milestone()
	```
	Problem is that there was no Due date. In fact, looking at the JSON dump, none of the milestones have a Due date, although some do have a Completed date. 
  * Now fixed - turns out the code wasn't even using the due date
  
### Stage 2c – dealing with trac users without github accounts ###

  * Some Trac users are the same as unrelated github accounts, so I had to do mapping of those.  I am using `username` -> `username-noaccount`. Since these usernames do not actually exist on Github, this caused all sorts of problems, which I fixed by brute force with a bunch of try-excepts. As a result the issues will be peppered with a bunch of "@username-noaccount" tags that do not resolve to users, but never mind.


### Stage 2d – making the tags more useful ###

  * Tags in github issues are used for lots of different Trac concepts: component, priority, keywords
  * It might be better if we gave single-letter prefixes to these, for instance:
      * `c:ionization-convergence`
      * `p:minor`
      * No prefix for keywords
  * There are some examples in the sample YAML config, but these were done by hand
  * I have now mainly done this. I wrote a script [utils/extract-tags.py](utils/extract-tags.py) that writes a YAML file of all the labels after removing spaces and commas and the like, then pasted it into the config file and did a bit of hand-editing. Here is a sample mapping from trac "types" to github "labels":
	```yaml
    type:
      '#color':           '0366d6'
      defect: t:defect
      defect - (web) documentation: t:defect:(web)-documentation
      defect - FPE: t:defect:FPE
      defect - code aborts: t:defect:code-aborts
      defect - convergence: t:defect:convergence
      defect - etc: t:defect:etc
      defect - failed assert: t:defect:failed-assert
      defect - wrong answer: t:defect:wrong-answer
      enhancement: t:enhancement
      physics: t:physics
      task: t:task
	```
	There are similar mappings for components, priorities, etc.
  * It still isn't perfect, but it will do for now.  Keywords are a bit all over the place. Some of them I have mapped to components. 
  * Also added some colors, but not all have shown up. 
  * Tested on tickets 101 to 140
  
###  TODO Stage 2e - importing the attachments ###
  * We should be able to do this as though they were comments
  * Github only allows file extensions of `.txt` plus various image and office formats
  * So we will have to add another `.txt` extension to `.in` and patch files 
  * To check what kind attachments are present, I wrote [utils/extract-attachments.py](utils/extract-attachments.py) to list the suffixes: 
	```
    pat:bug-tracker-migration-test will$ python utils/extract-attachments.py data/nublado-trac-export.json 
    {'', '.JPG', '.c', '.cpp', '.dat', '.diff', '.dr', '.gz', '.in', '.ini', '.inp',
     '.jpg', '.old', '.out', '.patch', '.pdf', '.png', '.rfi', '.szd', '.tgz',
     '.txt', '.vlg', '.xz', '.zip'}
	```
  * So we can divide them into 3 groups:
      1. Natively supported by github: .jpg, .png, .pdf, .txt, .zip, .gz (see [Github help docs](https://help.github.com/en/github/managing-your-work-on-github/file-attachments-on-issues-and-pull-requests))
      2. Can be treated as .gz file: .tgz
      3. Anything else can be treated as .txt file: .c, .cpp, .dat, .diff, .dr, .in, .ini, .inp, .old, .out, .patch, .rfi, .szd, .vlg, .xz
  * After reading all the API docs and perusing stackoverflow, it seems that there is no way to add *real* attachments using the API – however, there is a workaround:
      * Just add a link to the body of the issue to a file that is hosted elsewhere
      * Best place to host it would be in a repo dedicated to this purpose in @cloudy-bot's account, or just in the cloudy-astrophysics organization
          * [cloudy-astrophysics/trac-legacy-attachments](https://github.com/cloudy-astrophysics/trac-legacy-attachments)
      * So this nicely decouples the problem into a few steps
          1. For each ticket, get the attachments from Trac
          2. Save the actual files to the `trac-legacy-attachments` repo (organize in folders by ticket)
              * We can have the program write the files to a local directory, and then commit and push the changes to github by hand
          3. Add a link to the ticket when we import it into issues
      * The first two steps are now done in a new function `get_trac_attachments`, but I haven't tested it properly yet
