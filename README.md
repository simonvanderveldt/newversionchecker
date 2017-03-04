# New version checker

Simple stateless checking if a new version of a project is released. Should be run periodically.
If a new version is found an issue requesting a version bump will be created in a GitHub repository of choice.

Currently only supports git tags as source of information for new versions.


## How to use
- Create a `newversionchecker.toml` file with the following contents:

```toml
github_repo = "simonvanderveldt/newversionchecker" # Repo to create the version bump issues in
check_interval = 24 # Interval how often the check is scheduled to run (hours)

[projects] # Dictionary of projects to check and their git URL
"New version checker" = "https://github.com/simonvanderveldt/newversionchecker"
"<some other project>" = "https://github.com/<owner>/<some other project>"
```
- Create a [personal access token on GitHub](https://github.com/settings/tokens) with either `public_repo` or `repo` scope access
- Export the token as `GITHUB_API_TOKEN` environment variable
- Run `./newversionchecker.py`
