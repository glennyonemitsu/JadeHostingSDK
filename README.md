# Jade Hosting SDK

This is an SDK for a Jade powered website environment. This tool should enable the user to quickly setup a Jade environment and removing any needs for non-web programming languages such as python or ruby.

Jade can help people be incredibly productive, but the cost to learn how to implement it correctly for a site is a real hurdle to many who do not use it regularly. As a result people do not give Jade a chance because a "Hello, World!" example takes longer than the 30 seconds it would take in their native environment.

The main goal for this SDK is to make it as quick and painless as possible to begin making sites in Jade.
 
## Basic usage

```
# help output
$ python manager.py --help
$ python manager.py create --path test_project
# do some coding
$ python manager.py run_server --path test_project
```

## Project files
In directory test_project you will have the following directories:

- test_project/data
- test_project/scripts
- test_project/static
- test_project/static/css
- test_project/static/img
- test_project/static/js

And the file:

- test_project/app.yaml

### app.yaml 
app.yaml contains commented out code. In a nutshell you specify the route rule and the jade file associated with that rule. The following are a few rules you can use:

```
/
/about/
/members/<member_name>/
```

In that last route the variable "member_name" will be available in your jade file.

Each route can have one or more data files. These are static text files in the data/ directory that are either json or yaml format. The data/ directory does not need to be specified. Each succeeding data file with matching keys will overwrite keys in the preceeding file. 

Due to technical limitations, variables from route rules such as "member_name" above will be overwritten by any data files with the same key.

In the data/ directory just create files with a .json or .yaml extension and the SDK will properly load in the correct format. Due to json's strict formatting rules it is suggested to use the yaml format when possible.

Some completed routes are shown below:

```
routes:
  - rule: /
    script: home.jade
  - rule: /about-us/
    script: about-us.jade
    data: team.yaml
  - rule: /portfolio/
    script: portfolio.jade
    data: [projects.json, clients.yaml]
```

All static assets such as css and png files are to be in the static/ directory. Any url prefixed with /static/ will directly serve these files.

## Disclaimer
This is still alpha quality. Meaning features are rapidly experimented with and even removed based on user feedback. 
